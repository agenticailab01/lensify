"""Build a 'what we've been doing' capsule from session activity.

This is the dynamic counterpart to LENS.capsule.md:
    - LENS.capsule.md is STATIC — what the project looks like, written once
      per major change.
    - SESSION.capsule.md is DYNAMIC — what the agent has been DOING in the
      current chat, refreshed every N turns.

The session capsule replaces stale conversation tail. Instead of the agent
re-processing 8 turns of "I read X, then Y, then thought about Z" from raw
context, it reads a compressed list of the same facts.

Output budget: ≤ 600 tokens.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow both `from scripts.session_capsule import …` (tests) and
# `from session_capsule import …` (hooks that prepend the scripts dir).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from .session_state import (
        SessionState, EditRecord, ReadRecord, TestResult,
        active_modules, session_summary,
    )
    from .capsule import estimate_tokens, truncate_to_tokens
except ImportError:
    from session_state import (  # type: ignore[no-redef]
        SessionState, EditRecord, ReadRecord, TestResult,
        active_modules, session_summary,
    )
    from capsule import estimate_tokens, truncate_to_tokens  # type: ignore[no-redef]


SECTION_BUDGETS = {
    "header": 30,
    "active_modules": 80,
    "recent_edits": 180,
    "recent_reads": 120,
    "bash": 100,
    "tests": 90,
}
TOTAL_BUDGET = sum(SECTION_BUDGETS.values())   # 600 tokens


def _section_header(state: SessionState) -> str:
    summary = session_summary(state)
    return (
        "# SESSION ACTIVITY\n\n"
        f"Turn {summary['current_turn']} · "
        f"{summary['files_tracked']} files seen · "
        f"{summary['total_read_attempts']} read attempts · "
        f"{summary['duplicates_alerted']} duplicates avoided"
    )


def _section_active_modules(state: SessionState) -> str:
    am = active_modules(state, top_n=5)
    if not am:
        return ""
    lines = ["## Active modules"]
    for mod, score in am:
        lines.append(f"- `{mod}/` (score {score})")
    return "\n".join(lines)


def _section_recent_edits(state: SessionState) -> str:
    if not state.edits:
        return ""
    # Group by path, count
    by_path: dict[str, list[EditRecord]] = {}
    for e in state.edits[-50:]:
        by_path.setdefault(e.rel_path, []).append(e)
    rows = sorted(by_path.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]
    lines = ["## Recent edits"]
    for path, recs in rows:
        ops = ", ".join(sorted({r.op for r in recs}))
        last_turn = max(r.turn for r in recs)
        lines.append(f"- `{path}` — {ops}, {len(recs)}× (last turn {last_turn})")
    return "\n".join(lines)


def _section_recent_reads(state: SessionState) -> str:
    if not state.reads:
        return ""
    # Top-N by read_count
    rows = sorted(state.reads.values(), key=lambda r: r.read_count, reverse=True)[:6]
    lines = ["## Recently consulted files"]
    for r in rows:
        suffix = f", {r.read_count}× (dedup'd {r.read_count - 1})" if r.read_count > 1 else ""
        lines.append(f"- `{r.rel_path}` — first turn {r.first_turn}{suffix}")
    return "\n".join(lines)


def _section_bash(state: SessionState) -> str:
    if not state.bash_history:
        return ""
    recent = state.bash_history[-6:]
    lines = ["## Recent bash commands"]
    for b in recent:
        status = ""
        if b.exit_status is not None:
            status = " ✓" if b.exit_status == 0 else f" ✗ (exit {b.exit_status})"
        lines.append(f"- `{b.command}`{status}")
    return "\n".join(lines)


def _section_tests(state: SessionState) -> str:
    t = state.last_test
    if not t:
        return ""
    framework = t.framework
    if t.failed == 0 and t.passed > 0:
        line = f"## Last test run\n\n{framework}: **{t.passed} passed** (turn {t.turn})"
    elif t.failed > 0:
        line = (
            f"## Last test run\n\n"
            f"{framework}: **{t.failed} failed**, {t.passed} passed (turn {t.turn})"
        )
        if t.failing_tests:
            failed_list = "\n".join(f"- {n}" for n in t.failing_tests[:5])
            line = line + "\n\n" + failed_list
    else:
        line = f"## Last test run\n\n{framework}: no clear pass/fail signal (turn {t.turn})"
    return line


# Order — most useful first, dropped from the bottom when over budget
_SECTION_ORDER = [
    ("header", _section_header),
    ("active_modules", _section_active_modules),
    ("recent_edits", _section_recent_edits),
    ("tests", _section_tests),
    ("recent_reads", _section_recent_reads),
    ("bash", _section_bash),
]
# Order in which to truncate when over budget — least essential first
_TRUNCATE_ORDER = ["bash", "recent_reads", "tests", "recent_edits", "active_modules"]


def build_session_capsule(state: SessionState) -> str:
    """Compose SESSION.capsule.md content."""
    sections: dict[str, str] = {}
    for name, fn in _SECTION_ORDER:
        try:
            sections[name] = fn(state)
        except Exception:
            sections[name] = ""

    # Cap each section to its budget first
    for name, body in list(sections.items()):
        if body:
            sections[name] = truncate_to_tokens(body, SECTION_BUDGETS[name])

    # Then enforce total budget
    def total() -> int:
        return sum(estimate_tokens(s) for s in sections.values() if s)

    for name in _TRUNCATE_ORDER:
        if total() <= TOTAL_BUDGET:
            break
        if sections.get(name):
            sections[name] = ""

    body_parts = ["<!-- projectlens-session-begin -->"]
    for name, _ in _SECTION_ORDER:
        s = sections.get(name)
        if s:
            body_parts.append(s)
    body_parts.append("<!-- projectlens-session-end -->")
    return "\n\n".join(body_parts) + "\n"


def write_session_capsule(state: SessionState, project_root: str | Path) -> Path:
    """Write SESSION.capsule.md to projectlens-out/ in the project root."""
    out_dir = Path(project_root) / "projectlens-out"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "SESSION.capsule.md"
    target.write_text(build_session_capsule(state), encoding="utf-8")
    return target


def should_refresh(state: SessionState, every: int = 5) -> bool:
    """Decide if we're due for a session capsule refresh.

    Refresh triggers:
        - Every `every` turns (default 5)
        - At least 3 reads have been recorded
    """
    if state.current_turn == 0:
        return False
    if state.current_turn % every != 0:
        return False
    if len(state.reads) < 3:
        return False
    return True
