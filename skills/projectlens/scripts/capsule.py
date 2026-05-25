"""Capsule builder.

Produces LENS.capsule.md — the token-optimized context block that agents
ingest INSTEAD of reading raw files. Format is fixed Markdown; budgets are
enforced by the tier rules in complexity.py.
"""
from __future__ import annotations

try:
    from .complexity import TIER_BUDGETS
except ImportError:  # invoked as a script or via the hook sys.path trick
    from complexity import TIER_BUDGETS  # type: ignore[no-redef]


# Rough 4-char-per-token estimator. Replace with tiktoken when available.
def estimate_tokens(text: str) -> int:
    """Approximate token count for any text. Conservative estimate (slightly high)."""
    if not text:
        return 0
    # Markdown formatting roughly evens out — characters/4 is the standard estimate
    # for English + code. We use 3.5 to be slightly conservative.
    return max(1, int(len(text) / 3.5))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens, breaking on line boundaries when possible."""
    if estimate_tokens(text) <= max_tokens:
        return text
    target_chars = int(max_tokens * 3.5)
    if len(text) <= target_chars:
        return text
    # Try to break on a newline
    truncated = text[:target_chars]
    last_nl = truncated.rfind("\n")
    if last_nl > target_chars * 0.5:
        truncated = truncated[:last_nl]
    return truncated + "\n…\n"


def section_summary(lens_data: dict, tier: str) -> str:
    """Build the SUMMARY section."""
    project_kind = lens_data.get("project_kind", "codebase")
    primary = lens_data.get("primary_language", "mixed languages")
    files = lens_data.get("files", 0)
    loc = lens_data.get("loc", 0)
    line = f"# SUMMARY\n\n{project_kind} in {primary}; {files} files, {loc:,} LOC."
    return truncate_to_tokens(line, TIER_BUDGETS[tier]["summary"])


def section_entry(lens_data: dict, tier: str) -> str:
    """Build the ENTRY section listing main entry points."""
    entries = lens_data.get("entry_points", [])
    if not entries:
        return ""
    lines = ["## ENTRY"]
    cap = 3 if tier == "T1" else (8 if tier == "T2" else 15)
    for e in entries[:cap]:
        role = e.get("role", "entry")
        lines.append(f"- `{e['path']}` — {role}")
    return truncate_to_tokens("\n".join(lines), TIER_BUDGETS[tier]["entry"])


def section_modules(lens_data: dict, tier: str) -> str:
    """Build the MODULES section: directory → purpose."""
    modules = lens_data.get("modules", [])
    if not modules:
        return ""
    lines = ["## MODULES", "", "| Path | Purpose |", "|---|---|"]
    cap = 5 if tier == "T1" else (12 if tier == "T2" else 30)
    for m in modules[:cap]:
        purpose = m.get("purpose", "—")
        lines.append(f"| `{m['path']}` | {purpose} |")
    return truncate_to_tokens("\n".join(lines), TIER_BUDGETS[tier]["modules"])


def section_conventions(lens_data: dict, tier: str) -> str:
    """Build the CONVENTIONS section."""
    convs = lens_data.get("conventions", [])
    if not convs:
        return ""
    lines = ["## CONVENTIONS"]
    cap = 3 if tier == "T1" else (8 if tier == "T2" else 15)
    for c in convs[:cap]:
        lines.append(f"- {c}")
    return truncate_to_tokens("\n".join(lines), TIER_BUDGETS[tier]["conventions"])


def section_hotspots(lens_data: dict, tier: str) -> str:
    """Build the HOTSPOTS section from git churn data."""
    hotspots = lens_data.get("hotspots", [])
    if not hotspots:
        return ""
    lines = ["## HOTSPOTS", "", "| File | Churn | Last touched |", "|---|---|---|"]
    cap = 3 if tier == "T1" else (5 if tier == "T2" else 10)
    for h in hotspots[:cap]:
        commits = h.get("commits", 0)
        last = h.get("last_touched", "—")
        lines.append(f"| `{h['path']}` | {commits} commits | {last} |")
    return truncate_to_tokens("\n".join(lines), TIER_BUDGETS[tier]["hotspots"])


def section_risks(lens_data: dict, tier: str) -> str:
    """Build the RISKS section with confidence tags."""
    risks = lens_data.get("risks", [])
    if not risks:
        return ""
    lines = ["## RISKS"]
    cap = 3 if tier == "T1" else (6 if tier == "T2" else 12)
    for r in risks[:cap]:
        tag = r.get("confidence", "INFERRED")
        summary = r.get("summary", "—")
        lines.append(f"- [{tag}] {summary}")
    return truncate_to_tokens("\n".join(lines), TIER_BUDGETS[tier]["risks"])


def section_symbols(lens_data: dict, tier: str) -> str:
    """Build the SYMBOLS section — top-N public signatures.

    Skipped entirely on T1 (budget = 0). For T2/T3, shows up to 10/20 symbols
    formatted as `signature  (path:line)`.
    """
    budget = TIER_BUDGETS[tier].get("symbols", 0)
    if budget <= 0:
        return ""
    symbols = lens_data.get("symbols", [])
    if not symbols:
        return ""
    cap = 10 if tier == "T2" else 20
    lines = ["## SYMBOLS"]
    for s in symbols[:cap]:
        sig = s.get("signature", "")
        path = s.get("path", "")
        line = s.get("line", 0)
        if sig:
            loc = f"  ({path}:{line})" if path else ""
            lines.append(f"- `{sig}`{loc}")
    return truncate_to_tokens("\n".join(lines), budget)


# Section priority — lowest priority truncated first when over budget.
# Order: summary, entry, modules, symbols, frameworks (ROUTES/NOTEBOOKS/etc.),
# conventions, hotspots, risks.
SECTION_ORDER = [
    "summary", "entry", "modules", "symbols", "frameworks",
    "conventions", "hotspots", "risks",
]
# Truncate order — lowest priority first. Framework sections (high-value,
# framework-aware) drop before SYMBOLS but after RISKS.
TRUNCATE_ORDER = ["symbols", "frameworks", "risks", "hotspots", "modules", "conventions", "entry"]
# summary is never truncated.


def section_frameworks(lens_data: dict, tier: str) -> str:
    """Concatenate all pre-rendered framework adapter sections.

    `lens_data["framework_sections"]` is the list produced by
    frameworks.registry.render_adapter_sections() — each item already
    respects its per-adapter slice of the framework budget.
    """
    budget = TIER_BUDGETS[tier].get("frameworks", 0)
    if budget <= 0:
        return ""
    items = lens_data.get("framework_sections", []) or []
    if not items:
        return ""
    parts: list[str] = []
    for item in items:
        sec = item.get("section") if isinstance(item, dict) else None
        if sec:
            parts.append(sec)
    if not parts:
        return ""
    combined = "\n\n".join(parts)
    return truncate_to_tokens(combined, budget)


def build_section_dict(lens_data: dict, tier: str) -> dict[str, str]:
    """Build the section dict with truncation applied, but no wrapping markers.

    Returned dict is keyed by section name (lowercase) — useful for the
    selective-injection path which needs addressable sections.
    """
    if tier not in TIER_BUDGETS:
        raise ValueError(f"Unknown tier: {tier!r}")

    sections = {
        "summary": section_summary(lens_data, tier),
        "entry": section_entry(lens_data, tier),
        "modules": section_modules(lens_data, tier),
        "symbols": section_symbols(lens_data, tier),
        "frameworks": section_frameworks(lens_data, tier),
        "conventions": section_conventions(lens_data, tier),
        "hotspots": section_hotspots(lens_data, tier),
        "risks": section_risks(lens_data, tier),
    }
    budget = TIER_BUDGETS[tier]["total"]

    def total() -> int:
        return sum(estimate_tokens(s) for s in sections.values() if s)

    for name in TRUNCATE_ORDER:
        if total() <= budget:
            break
        if sections.get(name):
            sections[name] = ""
    return sections


def build_capsule(lens_data: dict, tier: str) -> str:
    """Compose the full capsule, enforcing total token budget.

    If sum-of-sections exceeds the total budget, truncate from the end of
    TRUNCATE_ORDER until it fits. SUMMARY is never truncated.
    """
    sections = build_section_dict(lens_data, tier)
    parts = ["<!-- projectlens-begin -->"]
    for name in SECTION_ORDER:
        s = sections.get(name)
        if s:
            parts.append(s)
    parts.append("<!-- projectlens-end -->")
    return "\n\n".join(parts) + "\n"


def build_addressable_sections(lens_data: dict, tier: str) -> dict:
    """Build a JSON-serializable dict of capsule sections + metadata.

    The output is written to projectlens-out/lens.sections.json so the
    UserPromptSubmit injection hook can pick relevant sections at runtime.
    """
    sections = build_section_dict(lens_data, tier)
    return {
        "version": 1,
        "tier": tier,
        "project_name": lens_data.get("project_name", ""),
        "primary_language": lens_data.get("primary_language"),
        "module_paths": [m.get("path", "").rstrip("/") for m in lens_data.get("modules", []) if m.get("path")],
        "entry_paths": [e.get("path", "") for e in lens_data.get("entry_points", []) if e.get("path")],
        "symbol_names": [s.get("name", "") for s in lens_data.get("symbols", []) if s.get("name")],
        "sections": {k: v for k, v in sections.items() if v},
    }


def install_into(capsule: str, target_file: str) -> tuple[bool, str]:
    """Insert or replace the capsule block in a CLAUDE.md / AGENTS.md file.

    Returns (was_inserted, message). Idempotent — replaces an existing block
    cleanly if present.
    """
    from pathlib import Path
    p = Path(target_file)
    BEGIN = "<!-- projectlens-begin -->"
    END = "<!-- projectlens-end -->"

    if not p.exists():
        p.write_text(capsule, encoding="utf-8")
        return True, f"created {target_file} with capsule"

    existing = p.read_text(encoding="utf-8")
    if BEGIN in existing and END in existing:
        before = existing.split(BEGIN, 1)[0].rstrip()
        after = existing.split(END, 1)[1].lstrip()
        new_content = (before + "\n\n" + capsule.strip() + "\n\n" + after).strip() + "\n"
        p.write_text(new_content, encoding="utf-8")
        return True, f"replaced capsule block in {target_file}"

    # Append at end
    new_content = existing.rstrip() + "\n\n" + capsule
    p.write_text(new_content, encoding="utf-8")
    return True, f"appended capsule to {target_file}"
