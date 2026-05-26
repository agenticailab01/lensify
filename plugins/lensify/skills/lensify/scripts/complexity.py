"""Complexity tier detection.

T1 Sketch:   < 50 files, < 5,000 LOC, single language, no nested modules
T2 Atlas:    50–1,000 files OR 5,000–100,000 LOC, multi-module
T3 Compass:  > 1,000 files OR > 100,000 LOC OR monorepo markers

The decision returns the tier plus a human-readable reason for transparency.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .walker import (
        WalkResult,
        detect_monorepo_markers,
        top_level_dirs,
    )
except ImportError:
    from walker import (  # type: ignore[no-redef]
        WalkResult,
        detect_monorepo_markers,
        top_level_dirs,
    )


@dataclass
class TierDecision:
    tier: str             # "T1" | "T2" | "T3"
    reason: str           # human-readable
    files: int
    loc: int
    languages: dict[str, int]
    primary_language: str | None
    primary_share: float  # 0..1
    top_dirs: list[str]
    monorepo_markers: list[str]

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "reason": self.reason,
            "files": self.files,
            "loc": self.loc,
            "languages": self.languages,
            "primary_language": self.primary_language,
            "primary_share": round(self.primary_share, 3),
            "top_dirs": self.top_dirs,
            "monorepo_markers": self.monorepo_markers,
        }


def decide(walk_result: WalkResult, override: str | None = None) -> TierDecision:
    """Pick a tier from a walk result, or honor an explicit override."""
    files = len(walk_result.code_files)
    loc = walk_result.total_loc
    langs = walk_result.language_breakdown
    primary_language = max(langs, key=langs.get) if langs else None
    primary_share = (langs[primary_language] / loc) if (primary_language and loc) else 0.0
    dirs = top_level_dirs(walk_result)
    monorepo = detect_monorepo_markers(Path(walk_result.root))

    if override in {"T1", "T2", "T3"}:
        return TierDecision(
            tier=override,
            reason=f"forced via override flag (--tier {override})",
            files=files, loc=loc, languages=langs,
            primary_language=primary_language, primary_share=primary_share,
            top_dirs=dirs, monorepo_markers=monorepo,
        )

    # T3 wins on any single strong signal
    if files > 1000 or loc > 100_000 or len(monorepo) >= 1 or len(dirs) >= 5:
        reasons = []
        if files > 1000:
            reasons.append(f"{files} files > 1000")
        if loc > 100_000:
            reasons.append(f"{loc:,} LOC > 100k")
        if monorepo:
            reasons.append(f"monorepo markers: {', '.join(monorepo)}")
        if len(dirs) >= 5:
            reasons.append(f"{len(dirs)} top-level module dirs")
        return TierDecision(
            tier="T3",
            reason="; ".join(reasons),
            files=files, loc=loc, languages=langs,
            primary_language=primary_language, primary_share=primary_share,
            top_dirs=dirs, monorepo_markers=monorepo,
        )

    # Empty / docs-only project: always T1
    if files == 0:
        return TierDecision(
            tier="T1",
            reason="no code files detected — docs-only or empty project",
            files=files, loc=loc, languages=langs,
            primary_language=primary_language, primary_share=primary_share,
            top_dirs=dirs, monorepo_markers=monorepo,
        )

    # T1 needs ALL signals to be small
    is_t1 = (
        files < 50
        and loc < 5000
        and primary_share >= 0.8
        and len(dirs) <= 2
    )
    if is_t1:
        return TierDecision(
            tier="T1",
            reason=f"small project: {files} files, {loc:,} LOC, primary lang {primary_language} ({primary_share:.0%})",
            files=files, loc=loc, languages=langs,
            primary_language=primary_language, primary_share=primary_share,
            top_dirs=dirs, monorepo_markers=monorepo,
        )

    # Otherwise T2
    return TierDecision(
        tier="T2",
        reason=f"medium project: {files} files, {loc:,} LOC, {len(dirs)} module dirs, primary lang {primary_language}",
        files=files, loc=loc, languages=langs,
        primary_language=primary_language, primary_share=primary_share,
        top_dirs=dirs, monorepo_markers=monorepo,
    )


# Token budgets per tier (used by capsule builder).
#
# T1 skips both symbols AND framework sections (too noisy for tiny projects).
# T2 + T3 budgets reserve a `frameworks` slot shared by all detected adapters.
# Adapter sections compete for that pool by priority.
#
# IMPORTANT: tests/benchmark_perf.py::test_capsule_token_budget_unchanged
# locks these totals in. Bumping them is intentional and must update the test.
TIER_BUDGETS = {
    "T1": {
        "total": 500,
        "summary": 30, "entry": 80, "modules": 200,
        "conventions": 80, "hotspots": 70, "risks": 40,
        "symbols": 0, "frameworks": 0,
    },
    "T2": {
        "total": 2100,
        "summary": 40, "entry": 150, "modules": 600,
        "conventions": 250, "hotspots": 300, "risks": 160,
        "symbols": 200, "frameworks": 400,
    },
    "T3": {
        "total": 3600,
        "summary": 60, "entry": 300, "modules": 1000,
        "conventions": 400, "hotspots": 500, "risks": 240,
        "symbols": 400, "frameworks": 700,
    },
}

# How many symbols to surface in the capsule, per tier
TIER_SYMBOL_LIMIT = {"T1": 0, "T2": 10, "T3": 20}
