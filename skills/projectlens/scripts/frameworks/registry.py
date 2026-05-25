"""Adapter discovery + dispatcher.

This module is the *only* place that imports adapter modules. Everything
else (scan.py, capsule.py) interacts with adapters through the result list
returned by `run_adapters()`.

Lazy-loading mechanics:
    1. Read manifest.json once per scan — a tiny JSON file mapping framework
       names to module paths.
    2. Build a flat set of imports across parsed files.
    3. Find manifest entries whose signature substring matches any import.
    4. import_module() ONLY the matched adapter modules.
    5. Instantiate and run extract() on each.

Result: 25 manifest entries cost ~5 ms of dispatch; only the relevant 2-3
modules actually get imported. Hook scripts never touch this code path.
"""
from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from .base import FrameworkAdapter, FrameworkInfo
except ImportError:
    from base import FrameworkAdapter, FrameworkInfo  # type: ignore[no-redef]


_FRAMEWORKS_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = _FRAMEWORKS_DIR / "manifest.json"
USER_FRAMEWORKS_DIRNAME = ".projectlens/frameworks"  # per-project drop-in


@dataclass
class ManifestEntry:
    name: str
    module: str                  # importable path, e.g. "_enterprise.fastapi"
    signatures: list[str]        # substrings to match against imports
    pack: str = "core"           # informational only

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "ManifestEntry":
        return cls(
            name=name,
            module=str(data.get("module", "")),
            signatures=list(data.get("signatures", []) or []),
            pack=str(data.get("pack", "core")),
        )


def load_manifest(path: Path | None = None) -> list[ManifestEntry]:
    """Read manifest.json. Tolerant of missing/corrupt file."""
    p = path or MANIFEST_PATH
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, dict):
        return []
    return [ManifestEntry.from_dict(name, entry) for name, entry in raw.items()
            if isinstance(entry, dict)]


def _collect_imports(parsed_files) -> set[str]:
    """One pass, one set, lower-cased. (Backwards-compat wrapper.)"""
    out: set[str] = set()
    for pf in parsed_files:
        for imp in getattr(pf, "imports", []) or []:
            if imp:
                # Normalize: take the top-level package name
                out.add(imp.lower().strip().split(".")[0])
    return out


_COMPOSE_FILENAMES = frozenset({
    "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml",
})


def _collect_signals(parsed_files, walk_result=None) -> set[str]:
    """Full signal set used for manifest matching.

    Includes:
        - Top-level import names (lower-cased), from parsed files
        - File extensions present (without the leading dot), from walk_result
        - For multi-dot config files like `tailwind.config.js`, the leading
          stem (`tailwind`) so adapters can match on config-file presence
        - The literal `docker-compose` signal when a compose file is found

    This lets adapters declare themselves by:
      • import pattern   (most frameworks — e.g. fastapi, sqlalchemy)
      • file extension   (e.g. Jupyter triggers on `.ipynb`, Vue on `.vue`)
      • config filename  (e.g. Tailwind on `tailwind.config.*`,
                          Docker Compose on `docker-compose.yml`)
    """
    signals = _collect_imports(parsed_files)
    if walk_result is not None:
        for rec in getattr(walk_result, "files", []) or []:
            ext = (rec.extension or "").lstrip(".").lower()
            if ext:
                signals.add(ext)
            path = getattr(rec, "path", "") or ""
            basename = path.rsplit("/", 1)[-1].lower()
            # Multi-dot pattern like `foo.config.js` → emit `foo` as a signal
            # so adapters with signature "foo" trigger on config presence.
            parts = basename.split(".")
            if len(parts) >= 3 and parts[0]:
                signals.add(parts[0])
            # Compose files don't follow the multi-dot pattern (`docker-compose.yml`
            # has only 2 segments after splitting on `.`), so special-case them.
            if basename in _COMPOSE_FILENAMES:
                signals.add("docker-compose")
    return signals


def match_manifest_to_imports(
    manifest: list[ManifestEntry],
    imports: set[str],
) -> list[ManifestEntry]:
    """Return the subset of manifest entries whose signatures match imports."""
    matched: list[ManifestEntry] = []
    for entry in manifest:
        for sig in entry.signatures:
            keyword = sig.replace("import ", "").replace("from ", "")
            keyword = keyword.strip().split(".")[0].lower()
            if keyword and keyword in imports:
                matched.append(entry)
                break
    return matched


def _import_adapter_module(module_path: str):
    """Import scripts.frameworks.<module_path>. Returns the module or None."""
    full = f"scripts.frameworks.{module_path}"
    try:
        return importlib.import_module(full)
    except ImportError:
        # Try the bare name (hook subprocess style)
        try:
            return importlib.import_module(module_path)
        except ImportError:
            return None


def _adapter_classes_in(module) -> list[type[FrameworkAdapter]]:
    """Find all FrameworkAdapter subclasses in a module."""
    out: list[type[FrameworkAdapter]] = []
    for attr in dir(module):
        if attr.startswith("_"):
            continue
        obj = getattr(module, attr)
        if (isinstance(obj, type)
                and issubclass(obj, FrameworkAdapter)
                and obj is not FrameworkAdapter):
            out.append(obj)
    return out


def discover_adapter_classes(
    parsed_files,
    *,
    manifest: list[ManifestEntry] | None = None,
    user_dir: Path | None = None,
    walk_result=None,
) -> list[type[FrameworkAdapter]]:
    """Return only the adapter classes relevant to this project.

    Order:
        1. Built-in manifest entries that match the project's signals
           (imports + file extensions)
        2. User-defined adapters in <project>/.projectlens/frameworks/*.py
    """
    manifest = manifest if manifest is not None else load_manifest()
    signals = _collect_signals(parsed_files, walk_result=walk_result)
    matched = match_manifest_to_imports(manifest, signals)

    out: list[type[FrameworkAdapter]] = []
    for entry in matched:
        mod = _import_adapter_module(entry.module)
        if mod is None:
            continue
        for cls in _adapter_classes_in(mod):
            errs = cls.validate_class()
            if errs:
                # Skip malformed adapters; never crash the scan
                continue
            out.append(cls)

    # User-defined adapters (per-project)
    if user_dir is not None:
        out.extend(_load_user_adapters(user_dir))

    return out


def _load_user_adapters(user_dir: Path) -> list[type[FrameworkAdapter]]:
    """Load any *.py files in <project>/.projectlens/frameworks/ as adapters.

    SECURITY — opt-in only.

    Loading user-defined adapters means importing arbitrary Python from
    whatever repo is being scanned. Scanning a malicious repo would let
    that repo execute code in the agent's environment. To avoid this:

      • By default (no env var set), this function returns [] without
        opening the directory.
      • Power users set PROJECTLENS_USER_ADAPTERS=1 in their shell rc to
        enable loading. They take responsibility for trusting the repos
        they scan.

    The env var name is intentionally long to make accidental enabling
    unlikely. Documentation in SECURITY.md spells out the threat model.
    """
    import os
    if os.environ.get("PROJECTLENS_USER_ADAPTERS", "").strip() != "1":
        return []
    if not user_dir.exists() or not user_dir.is_dir():
        return []
    # Put user_dir at the front of sys.path temporarily
    out: list[type[FrameworkAdapter]] = []
    str_user = str(user_dir)
    needs_remove = str_user not in sys.path
    if needs_remove:
        sys.path.insert(0, str_user)
    try:
        for py in user_dir.glob("*.py"):
            if py.name.startswith("_"):
                continue
            try:
                mod = importlib.import_module(py.stem)
            except Exception:  # noqa: BLE001 — never crash on a bad user adapter
                continue
            for cls in _adapter_classes_in(mod):
                if cls.validate_class():
                    continue
                out.append(cls)
    finally:
        if needs_remove:
            try:
                sys.path.remove(str_user)
            except ValueError:
                pass
    return out


def run_adapters(
    walk_result,
    parsed_files,
    *,
    project_root: Path | str | None = None,
    manifest: list[ManifestEntry] | None = None,
) -> list[FrameworkInfo]:
    """Top-level entry point used by scan.py.

    Returns a list of FrameworkInfo objects — one per detected adapter that
    successfully extracted. Order is by adapter priority desc.
    """
    user_dir = None
    if project_root is not None:
        user_dir = Path(project_root) / USER_FRAMEWORKS_DIRNAME

    classes = discover_adapter_classes(
        parsed_files, manifest=manifest, user_dir=user_dir,
        walk_result=walk_result,
    )

    infos: list[tuple[int, FrameworkInfo]] = []
    for cls in classes:
        try:
            instance = cls()
            info = instance.extract(walk_result, parsed_files)
            if isinstance(info, FrameworkInfo):
                # Enforce per-adapter cap on entries
                if len(info.entries) > cls.max_entries:
                    info.entries = info.entries[: cls.max_entries]
                infos.append((cls.priority, info))
        except Exception:  # noqa: BLE001
            # An adapter failing must never break the scan
            continue

    infos.sort(key=lambda kv: kv[0], reverse=True)
    return [info for _, info in infos]


def render_adapter_sections(
    walk_result,
    parsed_files,
    *,
    project_root: Path | str | None = None,
    total_budget_tokens: int = 200,
    manifest: list[ManifestEntry] | None = None,
) -> list[dict]:
    """Run all detected adapters and pre-render their capsule sections.

    The capsule builder consumes this list directly — it does not need to
    re-instantiate adapters. Each item is::
        {"name": str, "priority": int, "section": str, "info": dict}

    The budget is split *proportional to priority* across active adapters.
    Adapters that produce no section (capsule_section returns None) are
    excluded from the split so others get more room.
    """
    user_dir = None
    if project_root is not None:
        user_dir = Path(project_root) / USER_FRAMEWORKS_DIRNAME

    classes = discover_adapter_classes(
        parsed_files, manifest=manifest, user_dir=user_dir,
        walk_result=walk_result,
    )

    # First pass: extract + collect instances we'll render
    pending: list[tuple[type[FrameworkAdapter], FrameworkAdapter, FrameworkInfo]] = []
    for cls in classes:
        try:
            inst = cls()
            info = inst.extract(walk_result, parsed_files)
            if not isinstance(info, FrameworkInfo) or not info.entries:
                continue
            if len(info.entries) > cls.max_entries:
                info.entries = info.entries[: cls.max_entries]
            pending.append((cls, inst, info))
        except Exception:  # noqa: BLE001
            continue

    if not pending:
        return []

    # Budget split — weight by priority. Minimum 50 tok per adapter.
    weights = [max(1, cls.priority) for cls, _, _ in pending]
    total_weight = sum(weights) or 1
    rendered: list[dict] = []
    for (cls, inst, info), w in zip(pending, weights):
        slice_tokens = max(50, int(total_budget_tokens * w / total_weight))
        try:
            section = inst.capsule_section(info, budget_tokens=slice_tokens)
        except Exception:  # noqa: BLE001
            section = None
        if not section:
            continue
        rendered.append({
            "name": cls.name,
            "priority": cls.priority,
            "section": section,
            "info": info.to_dict(),
        })

    rendered.sort(key=lambda r: r["priority"], reverse=True)
    return rendered
