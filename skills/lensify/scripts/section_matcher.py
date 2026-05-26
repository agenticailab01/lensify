"""Pick the relevant capsule sections for a given user prompt.

Pure rule-based matching — keyword lookups + module-name detection. No LLM
call, no embeddings. The aim is to be fast (<5ms) and deterministic, not
perfect. When the matcher is unsure, it errs toward including more sections
(better the agent has extra context than too little).

Match scoring:
    Each section accumulates a score from keyword hits + module-name hits +
    intent-phrase hits. Sections with score > 0 are returned, ordered by
    relevance. If NO section scores, a safe default ("summary" + "modules")
    is returned.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


# Keywords that indicate intent toward a specific section.
# All keywords are case-insensitive; matched as whole words where reasonable.
SECTION_KEYWORDS = {
    "summary": [
        "what is this", "overview", "purpose", "project does", "high level",
        "in a sentence", "summary", "describe this", "tl;dr", "what does this do",
    ],
    "entry": [
        "run", "start", "execute", "launch", "boot", "deploy", "entry",
        "main", "command", "cli", "how do i run", "kick off", "fire up",
    ],
    "modules": [
        "where", "live", "find", "located", "module", "directory", "folder",
        "structure", "organized", "organisation", "package", "file lives",
    ],
    "conventions": [
        "convention", "style", "lint", "format", "standard", "coding standard",
        "pattern", "naming", "typing", "type hint", "rules", "guideline",
    ],
    "hotspots": [
        "active", "changing", "churn", "hot", "busy", "recent changes",
        "frequently modified", "where is the action",
    ],
    "risks": [
        "risk", "risks", "broken", "issue", "issues", "problem", "problems",
        "concern", "concerns", "danger", "smell", "cyclical", "dead code",
        "untested",
    ],
    "symbols": [
        # Specific symbol-intent phrases only. "what does X" alone is too
        # generic — we route via the symbol-name boost instead.
        "signature", "signatures", "type hint", "type of", "returns",
        "how do i call", "parameters of", "arguments of",
        "function signature", "method signature", "argument types",
        "what's the api", "what is the api", "call this function",
    ],
}

# Phrases that indicate the user is asking about session activity rather than
# the static lens — surface SESSION sections instead.
SESSION_INDICATORS = [
    "we just", "we did", "earlier in this session", "what have we done",
    "what did we change", "what files have we touched", "session activity",
    "current session", "so far", "previously in this chat",
]


@dataclass
class MatchResult:
    sections: list[str]            # ordered by score (highest first)
    scores: dict[str, int]         # section -> score
    matched_modules: list[str]     # module paths the prompt referenced
    needs_session: bool            # True if user is asking about session activity
    matched_symbols: list[str] = field(default_factory=list)  # symbol names the prompt referenced


def _word_boundary_search(needle: str, haystack: str) -> bool:
    """Word-aware substring match for short keywords; substring for phrases."""
    needle_low = needle.lower()
    haystack_low = haystack.lower()
    if " " in needle_low or len(needle_low) > 12:
        return needle_low in haystack_low
    # For short tokens, require word boundaries
    pattern = r"\b" + re.escape(needle_low) + r"\b"
    return re.search(pattern, haystack_low) is not None


def match(
    prompt: str,
    module_paths: Iterable[str] | None = None,
    symbol_names: Iterable[str] | None = None,
) -> MatchResult:
    """Score every section against the prompt.

    Args:
        prompt: the user's raw message text
        module_paths: known top-level module names (e.g., ["api", "domain", "db"])
                      from lens.sections.json — boosts MODULES when these appear
        symbol_names: known public symbol names from lens.sections.json —
                      mentioning one boosts SYMBOLS strongly
    """
    prompt = prompt or ""
    scores: dict[str, int] = {k: 0 for k in SECTION_KEYWORDS}
    matched_modules: list[str] = []
    matched_symbols: list[str] = []

    # Keyword hits
    for section, kws in SECTION_KEYWORDS.items():
        for kw in kws:
            if _word_boundary_search(kw, prompt):
                scores[section] += 2 if " " in kw else 1

    # Module-name hits boost MODULES strongly
    for mod in (module_paths or []):
        if not mod:
            continue
        base = mod.split("/")[0]
        if _word_boundary_search(base, prompt):
            matched_modules.append(base)
            scores["modules"] = scores.get("modules", 0) + 3

    # Symbol-name hits boost SYMBOLS strongly
    for sym in (symbol_names or []):
        if not sym:
            continue
        # Strip class qualifier — "UserService.find_by_email" → match "find_by_email"
        # but ALSO match the qualified form for completeness
        leaf = sym.split(".")[-1]
        if leaf and len(leaf) >= 3 and _word_boundary_search(leaf, prompt):
            matched_symbols.append(sym)
            scores["symbols"] = scores.get("symbols", 0) + 3
        elif "." in sym and _word_boundary_search(sym, prompt):
            matched_symbols.append(sym)
            scores["symbols"] = scores.get("symbols", 0) + 3

    # Session-activity intent
    needs_session = any(_word_boundary_search(p, prompt) for p in SESSION_INDICATORS)

    # Pick winners
    ranked = sorted(
        ((name, s) for name, s in scores.items() if s > 0),
        key=lambda kv: kv[1],
        reverse=True,
    )
    chosen = [n for n, _ in ranked]

    # Safe default — when nothing matched and the prompt is non-trivial,
    # provide SUMMARY + MODULES (the most generally useful pair)
    if not chosen and len(prompt.strip()) > 2:
        chosen = ["summary", "modules"]

    return MatchResult(
        sections=chosen,
        scores=scores,
        matched_modules=matched_modules,
        needs_session=needs_session,
        matched_symbols=matched_symbols,
    )


# Selection cap — never inject all 6 sections; that defeats the point
MAX_SECTIONS = 4


def cap(result: MatchResult, max_sections: int = MAX_SECTIONS) -> list[str]:
    """Limit the chosen section count, keeping highest-score ones."""
    return result.sections[:max_sections]
