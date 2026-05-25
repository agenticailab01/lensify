"""Main entry point for ProjectLens.

Usage:
    python -m scripts.scan <path> [--tier T1|T2|T3|auto] [--capsule-only]
                                  [--ast-only] [--output DIR] [--no-git]

Writes to <path>/projectlens-out/:
    - LENS.html
    - LENS.capsule.md
    - lens.json (full structured data)
    - manifest.json (file hashes for stale-detection)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

# Allow `python scan.py` to work as well as `python -m scripts.scan`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.walker import walk
    from scripts.complexity import decide, TIER_BUDGETS
    from scripts.ast_parser import parse_all, detect_entry_points, detect_shape
    from scripts.git_analyzer import analyze_hotspots, churn_share
    from scripts.narrative import (
        collect_framework_hints, guess_project_kind,
        template_narrative, detect_risks,
    )
    from scripts.capsule import build_capsule, estimate_tokens, build_addressable_sections
    from scripts.lens_html import build_html
    from scripts.symbols import find_top_symbols, symbols_to_dicts
    try:
        from scripts.stats import record_event as _record_event
    except ImportError:
        _record_event = None
    try:
        from scripts.frameworks.registry import render_adapter_sections
    except ImportError:
        render_adapter_sections = None
else:
    from .walker import walk
    from .complexity import decide, TIER_BUDGETS
    from .ast_parser import parse_all, detect_entry_points, detect_shape
    from .git_analyzer import analyze_hotspots, churn_share
    from .narrative import (
        collect_framework_hints, guess_project_kind,
        template_narrative, detect_risks,
    )
    from .capsule import build_capsule, estimate_tokens, build_addressable_sections
    from .lens_html import build_html
    from .symbols import find_top_symbols, symbols_to_dicts
    try:
        from .stats import record_event as _record_event
    except ImportError:
        _record_event = None
    try:
        from .frameworks.registry import render_adapter_sections
    except ImportError:
        render_adapter_sections = None


VERSION = "0.15.0"


def _hash_files(records) -> dict[str, str]:
    """Return {path: sha256-short} for stale-detection."""
    out: dict[str, str] = {}
    for r in records:
        try:
            with open(r.abs_path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()[:16]
            out[r.path] = h
        except OSError:
            continue
    return out


def _infer_module_purpose(name: str, parsed_in_module: list) -> str:
    """Best-effort one-line purpose for a top-level module directory."""
    n = name.lower()
    common = {
        "api": "HTTP route handlers, request/response shapes",
        "routes": "URL → handler bindings",
        "domain": "business logic, pure functions",
        "core": "shared logic and utilities",
        "db": "database models and repositories",
        "models": "data models / ORM definitions",
        "repository": "data-access layer",
        "auth": "authentication and authorization",
        "tests": "test suite",
        "test": "test suite",
        "scripts": "operational scripts and tooling",
        "tools": "developer tooling",
        "ui": "user interface components",
        "components": "UI components",
        "pages": "page-level routes/views",
        "lib": "shared libraries",
        "utils": "utility functions",
        "config": "configuration loading",
        "worker": "background job workers",
        "jobs": "scheduled or queued jobs",
        "services": "service implementations",
        "client": "API client code",
        "server": "server implementation",
        "docs": "documentation",
        "migrations": "database migrations",
        "static": "static assets",
        "public": "public assets",
        "i18n": "internationalization",
    }
    if n in common:
        return common[n]
    # Fall back to "N files; languages: X, Y"
    langs: dict[str, int] = {}
    for pf in parsed_in_module:
        if pf.language:
            langs[pf.language] = langs.get(pf.language, 0) + 1
    if langs:
        lang_str = ", ".join(sorted(langs, key=langs.get, reverse=True)[:2])
        return f"{len(parsed_in_module)} files, {lang_str}"
    return f"{len(parsed_in_module)} files"


def _extract_conventions(root: Path) -> list[str]:
    """Pull conventions from common config files."""
    convs: list[str] = []
    # Linters / formatters
    if (root / "pyproject.toml").exists():
        content = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
        if "[tool.ruff]" in content:
            convs.append("Ruff for linting")
        if "[tool.black]" in content:
            convs.append("Black for formatting")
        if "[tool.mypy]" in content:
            convs.append("mypy type checking")
        if "[tool.pytest" in content:
            convs.append("pytest for tests")
    if (root / ".eslintrc.js").exists() or (root / ".eslintrc.json").exists():
        convs.append("ESLint for JS/TS linting")
    if (root / ".prettierrc").exists() or (root / ".prettierrc.json").exists():
        convs.append("Prettier for formatting")
    if (root / "tsconfig.json").exists():
        convs.append("TypeScript strict mode (check tsconfig.json)")
    if (root / "Dockerfile").exists():
        convs.append("Containerized via Dockerfile")
    if (root / ".github" / "workflows").is_dir():
        convs.append("CI via GitHub Actions")
    return convs


def scan(
    target: str,
    *,
    tier_override: str | None = None,
    capsule_only: bool = False,
    ast_only: bool = False,
    no_git: bool = False,
    output_dir: str | None = None,
) -> dict:
    """Run a full scan and write artefacts. Returns the lens_data dict."""
    t0 = time.time()
    target_path = Path(target).resolve()
    out_dir = Path(output_dir) if output_dir else target_path / "projectlens-out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Walk
    walk_result = walk(str(target_path))
    if not walk_result.code_files:
        # Empty / docs-only project
        decision_dict = {
            "tier": "T1", "reason": "no code files found",
            "files": 0, "loc": 0, "languages": {}, "primary_language": None,
            "primary_share": 0.0, "top_dirs": [], "monorepo_markers": [],
        }
        lens_data = {
            "project_name": target_path.name,
            "tier": "T1",
            "tier_decision": decision_dict,
            "summary": f"Empty or docs-only directory: {target_path.name}",
            "primary_language": None,
            "files": 0, "loc": 0,
            "modules": [], "entry_points": [], "hotspots": [], "risks": [],
            "conventions": [], "top_dirs": [],
            "shape": {"shape": "flat", "confidence": "forced", "evidence": []},
            "narrative": "This directory contains no recognized code files.",
            "capsule_tokens": 0,
            "version": VERSION,
        }
        _write_outputs(out_dir, lens_data, build_capsule(lens_data, "T1"), capsule_only)
        return lens_data

    # 2. Complexity tier
    decision = decide(walk_result, override=tier_override)
    tier = decision.tier

    # 3. Parse code
    parsed = parse_all(walk_result.code_files)
    parsed_dicts = [p.to_dict() for p in parsed]

    # 4. Entry points + shape
    entries = detect_entry_points(parsed)
    shape = detect_shape(parsed, decision.top_dirs)

    # 5. Hotspots from git
    hotspots = []
    if not no_git:
        hotspots = [h.to_dict() for h in analyze_hotspots(str(target_path), days=90, top=10)]
    churn = churn_share([type("H", (), h)() for h in hotspots]) if hotspots else 0.0

    # 6. Build modules list
    modules: list[dict] = []
    by_dir: dict[str, list] = {}
    for p in parsed:
        top = p.path.split("/")[0]
        if "/" in p.path:
            by_dir.setdefault(top, []).append(p)
    for name in sorted(by_dir.keys()):
        modules.append({
            "path": name + "/",
            "purpose": _infer_module_purpose(name, by_dir[name]),
            "files": len(by_dir[name]),
        })

    # 7. Conventions
    conventions = _extract_conventions(target_path)

    # 8. Risks
    risks = detect_risks(modules, parsed_dicts)

    # 8b. Top public symbols (Phase 5) — skip for T1 (budget = 0)
    symbol_limit = {"T1": 0, "T2": 10, "T3": 20}.get(tier, 0)
    symbols_list = []
    if symbol_limit > 0:
        try:
            top_syms = find_top_symbols(walk_result.code_files, parsed, top_n=symbol_limit)
            symbols_list = symbols_to_dicts(top_syms)
        except Exception:
            symbols_list = []  # never fail the scan on a symbol extraction bug

    # 8c. Framework adapter sections (Phase 9) — pre-rendered for the capsule
    framework_sections = []
    if render_adapter_sections is not None:
        try:
            framework_sections = render_adapter_sections(
                walk_result, parsed,
                project_root=target_path,
                total_budget_tokens=TIER_BUDGETS[tier].get("frameworks", 0),
            )
        except Exception:
            framework_sections = []

    # 9. Project kind + summary
    hints = collect_framework_hints(modules, entries)
    project_kind = guess_project_kind(decision.primary_language, hints)
    summary = (
        f"{project_kind} in {decision.primary_language or 'mixed languages'}; "
        f"{decision.files} files, {decision.loc:,} LOC across {len(decision.top_dirs)} module(s)."
    )

    # 10. Narrative (template fallback — LLM version handled by the skill flow)
    entry_path = entries[0]["path"] if entries else None
    narrative = template_narrative(
        project_kind=project_kind,
        primary_language=decision.primary_language,
        shape=shape["shape"],
        n_modules=len(modules),
        hotspots=hotspots,
        churn_pct=churn,
        risks=risks,
        entry_path=entry_path,
    )

    # 11. Assemble lens_data
    lens_data = {
        "project_name": target_path.name,
        "tier": tier,
        "tier_decision": decision.to_dict(),
        "summary": summary,
        "project_kind": project_kind,
        "primary_language": decision.primary_language,
        "files": decision.files,
        "loc": decision.loc,
        "modules": modules,
        "entry_points": entries,
        "hotspots": hotspots,
        "risks": risks,
        "conventions": conventions,
        "top_dirs": decision.top_dirs,
        "shape": shape,
        "narrative": narrative,
        "symbols": symbols_list,
        "framework_sections": framework_sections,
        "version": VERSION,
        "scan_seconds": round(time.time() - t0, 2),
    }

    # 12. Build capsule + measure tokens
    capsule = build_capsule(lens_data, tier)
    lens_data["capsule_tokens"] = estimate_tokens(capsule)

    # 13. Write outputs
    _write_outputs(out_dir, lens_data, capsule, capsule_only)

    # 14. Phase 8 telemetry — count the scan
    if _record_event is not None:
        try:
            _record_event("scan", project_root=str(target_path))
        except Exception:  # noqa: BLE001
            pass

    # 15. Banner line for the calling skill
    banner = {
        "tier": tier,
        "files": decision.files,
        "loc": decision.loc,
        "capsule_tokens": lens_data["capsule_tokens"],
        "output_dir": str(out_dir),
        "scan_seconds": lens_data["scan_seconds"],
    }
    print(json.dumps(banner))

    return lens_data


def _write_outputs(out_dir: Path, lens_data: dict, capsule: str, capsule_only: bool) -> None:
    """Write all output artefacts."""
    (out_dir / "LENS.capsule.md").write_text(capsule, encoding="utf-8")
    (out_dir / "lens.json").write_text(
        json.dumps(lens_data, indent=2, default=str),
        encoding="utf-8",
    )
    # Addressable sections for selective injection (Phase 3)
    try:
        tier = lens_data.get("tier", "T2")
        sections = build_addressable_sections(lens_data, tier)
        (out_dir / "lens.sections.json").write_text(
            json.dumps(sections, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # selective injection is optional — never fail the main scan
    if not capsule_only:
        html = build_html(lens_data, version=VERSION)
        (out_dir / "LENS.html").write_text(html, encoding="utf-8")
    # Manifest for stale-detection — hash the source files this lens covered
    manifest = {
        "version": VERSION,
        "generated_at": time.time(),
        "tier": lens_data.get("tier"),
        "summary": lens_data.get("summary"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProjectLens — one-page adaptive project lens.")
    parser.add_argument("target", help="Path to scan")
    parser.add_argument("--tier", choices=["T1", "T2", "T3", "auto"], default="auto",
                        help="Force a complexity tier (default: auto)")
    parser.add_argument("--capsule-only", action="store_true",
                        help="Skip HTML, write only the capsule")
    parser.add_argument("--ast-only", action="store_true",
                        help="Deterministic mode — no LLM enrichment of narrative")
    parser.add_argument("--no-git", action="store_true",
                        help="Skip git hotspot analysis")
    parser.add_argument("--output", default=None,
                        help="Override output directory (default: <target>/projectlens-out)")
    parser.add_argument("--install-agents-md", default=None, metavar="FILE", nargs="?",
                        const="AGENTS.md",
                        help="After scan, append/update the capsule inside a context file "
                             "(default: AGENTS.md; pass any path, e.g. CLAUDE.md, "
                             "GEMINI.md, .cursorrules)")
    parser.add_argument("--version", action="version", version=f"projectlens {VERSION}")
    args = parser.parse_args(argv)

    override = None if args.tier == "auto" else args.tier
    try:
        scan(
            args.target,
            tier_override=override,
            capsule_only=args.capsule_only,
            ast_only=args.ast_only,
            no_git=args.no_git,
            output_dir=args.output,
        )
    except (FileNotFoundError, NotADirectoryError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2

    # --install-agents-md: write/refresh the capsule inside a context file the
    # target tool reads. Idempotent via begin/end markers (install_into).
    if args.install_agents_md:
        try:
            from pathlib import Path
            try:
                from .capsule import install_into
            except ImportError:
                from capsule import install_into  # type: ignore[no-redef]
            target_path = Path(args.target).resolve()
            out_dir = (Path(args.output) if args.output
                       else target_path / "projectlens-out")
            capsule_path = out_dir / "LENS.capsule.md"
            if not capsule_path.exists():
                print(json.dumps({"error": "capsule not found", "path": str(capsule_path)}),
                      file=sys.stderr)
                return 3
            capsule_text = capsule_path.read_text(encoding="utf-8")
            agents_file = args.install_agents_md
            agents_path = (Path(agents_file)
                           if Path(agents_file).is_absolute()
                           else target_path / agents_file)
            _, msg = install_into(capsule_text, str(agents_path))
            print(json.dumps({"installed": str(agents_path), "result": msg}))
        except OSError as e:
            print(json.dumps({"error": f"install failed: {e}"}), file=sys.stderr)
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
