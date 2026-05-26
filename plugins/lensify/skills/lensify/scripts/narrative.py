"""Narrative generation — template-based fallback.

The LLM-driven narrative lives in the SKILL.md flow; this script provides the
deterministic `--ast-only` fallback. The fallback is intentionally shorter
(~80 words) so users running offline still get *something* readable.
"""
from __future__ import annotations


# Project kind heuristics: from primary language + manifest files
KIND_HINTS = {
    "Python+fastapi": "Python web API",
    "Python+django": "Python web application",
    "Python+flask": "Python web service",
    "Python+pytest": "Python library",
    "TypeScript+react": "TypeScript frontend",
    "JavaScript+react": "JavaScript frontend",
    "TypeScript+next": "Next.js web application",
    "TypeScript+express": "Node.js API",
    "JavaScript+express": "Node.js API",
    "Go+gin": "Go web service",
    "Go+grpc": "Go gRPC service",
    "Java+spring": "Java Spring service",
    "Rust+actix": "Rust web service",
}


def guess_project_kind(primary_language: str | None, hints: set[str]) -> str:
    """Pick a 'project kind' label from language + framework hints."""
    if not primary_language:
        return "codebase"
    for key, label in KIND_HINTS.items():
        lang, framework = key.split("+", 1)
        if lang == primary_language and framework in hints:
            return label
    return f"{primary_language} project"


def collect_framework_hints(modules: list[dict], entries: list[dict]) -> set[str]:
    """Scan module/entry names for known framework keywords."""
    keywords = {
        "fastapi", "django", "flask", "react", "next", "express",
        "gin", "grpc", "spring", "actix", "pytest", "vue", "svelte",
    }
    hints: set[str] = set()
    for thing in [*[m.get("path", "") for m in modules], *[e.get("path", "") for e in entries]]:
        low = thing.lower()
        for k in keywords:
            if k in low:
                hints.add(k)
    return hints


def template_narrative(
    *,
    project_kind: str,
    primary_language: str | None,
    shape: str,
    n_modules: int,
    hotspots: list[dict],
    churn_pct: float,
    risks: list[dict],
    entry_path: str | None,
) -> str:
    """Build an ~80-word narrative from structured inputs.

    No bullet points. Plain prose. Deterministic output for the same input.
    """
    shape_phrase = {
        "layered": "as a layered architecture (presentation, domain, data)",
        "hub-spoke": "around a central shared module that the rest depends on",
        "pipeline": "as a pipeline of sequential stages",
        "domain-map": "as a monorepo with multiple loosely-coupled domains",
        "flat": "as a flat collection of modules without strong hierarchy",
    }.get(shape, "as a collection of modules")

    hotspot_part = ""
    if hotspots:
        names = [h["path"].split("/")[-1] for h in hotspots[:2]]
        if len(names) == 1:
            hotspot_part = f" The most active area is {names[0]}, which sees frequent change."
        else:
            pct = int(churn_pct * 100) if churn_pct else 0
            hotspot_part = (
                f" The most active areas are {names[0]} and {names[1]}, which together "
                f"account for roughly {pct}% of recent commits."
            )

    risk_part = ""
    if risks:
        risk_part = f" Note that {risks[0].get('summary', 'one inferred risk')} appears worth checking."

    entry_part = ""
    if entry_path:
        entry_part = f" To get oriented, open {entry_path} first — that is where the application starts."

    return (
        f"This project is a {project_kind} organized {shape_phrase} across {n_modules} top-level modules."
        f"{hotspot_part}{risk_part}{entry_part}"
    ).strip()


def detect_risks(modules: list[dict], parsed_files: list[dict]) -> list[dict]:
    """Detect simple structural risks. Each risk carries a confidence tag.

    Risks:
        - EXTRACTED: untested modules (no matching test file)
        - EXTRACTED: cyclical imports between two modules
        - INFERRED: a module that hasn't been touched in a long time (needs git, skipped here)
        - AMBIGUOUS: empty or near-empty modules
    """
    risks: list[dict] = []

    # 1. Cyclical imports between top-level modules
    module_imports: dict[str, set[str]] = {}
    for pf in parsed_files:
        path = pf.get("path", "")
        if "/" not in path:
            continue
        top = path.split("/")[0]
        module_imports.setdefault(top, set())
        for imp in pf.get("imports", []):
            # Heuristic: if an import name matches another top-level module, count it
            module_imports[top].add(imp)

    top_names = set(module_imports.keys())
    seen_pairs: set[tuple[str, str]] = set()
    for a, imps in module_imports.items():
        for b in imps:
            if b in top_names and b != a:
                if (b, a) in seen_pairs:
                    continue
                if a in module_imports.get(b, set()):
                    risks.append({
                        "kind": "cyclical_imports",
                        "confidence": "EXTRACTED",
                        "summary": f"cyclical imports between `{a}` and `{b}`",
                    })
                    seen_pairs.add((a, b))

    # 2. Empty or near-empty modules (< 3 code files)
    counts: dict[str, int] = {}
    for pf in parsed_files:
        top = pf.get("path", "").split("/")[0]
        if top:
            counts[top] = counts.get(top, 0) + 1
    for mod, c in counts.items():
        if c < 3:
            risks.append({
                "kind": "thin_module",
                "confidence": "AMBIGUOUS",
                "summary": f"module `{mod}` has only {c} file(s) — possibly stub or dead",
            })

    return risks[:10]  # cap
