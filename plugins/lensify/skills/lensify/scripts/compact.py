"""Conversation Compactor (Phase 4).

Produces WORKING_CONTEXT.md — a compact summary of the current session that
the user can paste into a fresh chat to continue working without re-loading
the full conversation history. Token reclaim averages 8,000-25,000 tokens
per invocation depending on session length.

Two modes:
    - Deterministic (default): builds from session_state only, no API calls.
    - LLM-enhanced (--llm or env LENSIFY_COMPACT_LLM=1): asks Claude
      Haiku ONCE to add a 3-sentence narrative + suggested next steps.

Usage:
    python compact.py <project-path>                # deterministic
    python compact.py <project-path> --llm          # +Haiku enhancement
    python compact.py <project-path> --json         # machine-readable

Output: writes lensify-out/WORKING_CONTEXT.md and prints a banner JSON
on stdout for the calling skill to parse.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from .session_state import (
        load_state, SessionState, active_modules, session_summary,
    )
    from .session_capsule import build_session_capsule
    from .llm_client import call_claude, is_available, estimate_cost_usd
    from .memory import memory_from_session_state, save_memory, is_disabled as memory_disabled
    try:
        from .stats import record_event as _record_event
    except ImportError:
        _record_event = None
except ImportError:
    from session_state import (  # type: ignore[no-redef]
        load_state, SessionState, active_modules, session_summary,
    )
    from session_capsule import build_session_capsule  # type: ignore[no-redef]
    from llm_client import call_claude, is_available, estimate_cost_usd  # type: ignore[no-redef]
    from memory import memory_from_session_state, save_memory, is_disabled as memory_disabled  # type: ignore[no-redef]
    try:
        from stats import record_event as _record_event  # type: ignore[no-redef]
    except ImportError:
        _record_event = None  # type: ignore[no-redef]


# Average tokens per file an agent reads — same constant the benchmark uses.
AVG_TOKENS_PER_FILE_READ = 350
# Approximate tokens in a conversation turn (user + assistant + tool calls)
AVG_TOKENS_PER_TURN = 1_800


LLM_SYSTEM_PROMPT = (
    "You are summarizing what was being worked on in a coding session, based "
    "on a structured activity log. Be terse: no preamble, no apology, just "
    "the facts. Use the structure requested exactly."
)


def _llm_prompt_from_state(state: SessionState) -> str:
    """Construct the prompt fed to Claude for the narrative + next-step section."""
    summary = session_summary(state)
    mods = active_modules(state, top_n=5)
    edits_recent = state.edits[-12:]
    bash_recent = state.bash_history[-6:]

    payload = {
        "turn": summary["current_turn"],
        "files_seen": summary["files_tracked"],
        "duplicates_avoided": summary["duplicates_alerted"],
        "active_modules": [{"name": m, "score": s} for m, s in mods],
        "recent_edits": [{"path": e.rel_path, "op": e.op, "turn": e.turn}
                         for e in edits_recent],
        "recent_bash": [{"cmd": b.command, "exit": b.exit_status}
                        for b in bash_recent],
        "last_test": state.last_test.to_dict() if state.last_test else None,
    }
    return (
        "Given this structured activity log from a coding session, produce "
        "EXACTLY this Markdown structure (no extra sections, no apologies, "
        "no preamble):\n\n"
        "## What we were doing\n\n"
        "<one paragraph, 3-4 sentences, in plain prose>\n\n"
        "## Decisions / state-of-play\n\n"
        "- <fact or decision, inferred from edits/tests>\n"
        "- <fact or decision>\n"
        "- <fact or decision>\n\n"
        "## Suggested next step\n\n"
        "<one sentence — the most useful next action given the state>\n\n"
        "Activity log:\n```json\n"
        + json.dumps(payload, indent=2)
        + "\n```"
    )


def _section_overview(state: SessionState) -> str:
    summary = session_summary(state)
    duration = time.time() - state.started_at
    minutes = max(1, int(duration / 60))
    return (
        "## Session overview\n\n"
        f"- Turn: **{summary['current_turn']}**\n"
        f"- Duration: ~{minutes} min\n"
        f"- Files consulted: {summary['files_tracked']}\n"
        f"- Total read attempts: {summary['total_read_attempts']} "
        f"(dedup avoided {summary['duplicates_alerted']})\n"
        f"- Session ID: `{summary['session_id'] or 'n/a'}`"
    )


def _section_activity(state: SessionState) -> str:
    """Build the deterministic activity recap — same as session_capsule but
    longer-form and without the budget cap."""
    parts: list[str] = []

    mods = active_modules(state, top_n=8)
    if mods:
        parts.append("## Active modules")
        for name, score in mods:
            parts.append(f"- `{name}/` (activity score {score})")

    if state.edits:
        parts.append("\n## Files touched")
        # Group by path, count ops
        by_path: dict[str, dict] = {}
        for e in state.edits:
            entry = by_path.setdefault(e.rel_path, {"ops": set(), "count": 0, "last_turn": 0})
            entry["ops"].add(e.op)
            entry["count"] += 1
            entry["last_turn"] = max(entry["last_turn"], e.turn)
        # Sort by count desc
        for path, info in sorted(by_path.items(), key=lambda kv: kv[1]["count"], reverse=True)[:15]:
            ops = ", ".join(sorted(info["ops"]))
            parts.append(f"- `{path}` — {ops}, {info['count']}× (last turn {info['last_turn']})")

    if state.last_test:
        t = state.last_test
        parts.append("\n## Last test run")
        if t.failed > 0:
            parts.append(f"- {t.framework}: **{t.failed} failed**, {t.passed} passed (turn {t.turn})")
            if t.failing_tests:
                parts.append("- Failing:")
                for n in t.failing_tests[:8]:
                    parts.append(f"  - `{n}`")
        elif t.passed > 0:
            parts.append(f"- {t.framework}: **{t.passed} passed** (turn {t.turn})")
        else:
            parts.append(f"- {t.framework}: no clear pass/fail (turn {t.turn})")

    if state.bash_history:
        parts.append("\n## Recent commands")
        for b in state.bash_history[-10:]:
            status = ""
            if b.exit_status is not None:
                status = " ✓" if b.exit_status == 0 else f" ✗ ({b.exit_status})"
            parts.append(f"- `{b.command}`{status}")

    return "\n".join(parts) if parts else ""


def _section_consulted_files(state: SessionState) -> str:
    if not state.reads:
        return ""
    rows = sorted(state.reads.values(), key=lambda r: r.read_count, reverse=True)[:10]
    lines = ["## Files consulted"]
    for r in rows:
        dedup_note = f", {r.read_count}× (dedup avoided {r.read_count - 1})" if r.read_count > 1 else ""
        lines.append(f"- `{r.rel_path}` — first turn {r.first_turn}{dedup_note}")
    return "\n".join(lines)


def _section_llm_narrative(state: SessionState, *, use_llm: bool) -> tuple[str, dict | None]:
    """Return (markdown, llm_meta-or-None). When use_llm is False or no key
    is set, returns a placeholder note and None meta.
    """
    if not use_llm:
        return ("", None)
    if not is_available():
        return (
            "## Narrative\n\n"
            "_LLM enhancement requested but `ANTHROPIC_API_KEY` is not set; "
            "showing deterministic activity only._",
            None,
        )

    prompt = _llm_prompt_from_state(state)
    result = call_claude(prompt, system=LLM_SYSTEM_PROMPT, max_tokens=600)
    if not result.ok or not result.text:
        # Failure path — llm_meta is None so the caller marks llm_enhanced=False
        return (
            "## Narrative\n\n"
            f"_LLM call failed ({result.error or 'unknown'}); showing "
            "deterministic activity only._",
            None,
        )

    meta = {
        "duration": result.duration_seconds,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }
    if result.input_tokens is not None and result.output_tokens is not None:
        meta["est_usd"] = estimate_cost_usd(result.input_tokens, result.output_tokens)
    return (result.text.strip(), meta)


def estimate_tokens_reclaimed(state: SessionState) -> int:
    """Rough estimate of how many tokens were sitting in the conversation
    history that the compactor's WORKING_CONTEXT.md replaces.

    Approximation: each turn adds ~AVG_TOKENS_PER_TURN to the conversation
    buffer. After compaction, the user starts fresh with just the working
    context (~600-1,500 tokens). So reclaim ≈ turns × per-turn-tokens − 1,000.
    """
    turns = state.current_turn
    if turns < 2:
        return 0
    raw = turns * AVG_TOKENS_PER_TURN
    return max(0, raw - 1_000)


def build_working_context(state: SessionState, *, use_llm: bool = False) -> tuple[str, dict]:
    """Compose WORKING_CONTEXT.md.

    Returns (markdown_text, metadata_dict).
    """
    narrative, llm_meta = _section_llm_narrative(state, use_llm=use_llm)

    sections = [
        f"# Working Context — lensify v0.15.0\n\n"
        f"_Auto-generated {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} "
        f"to replace stale conversation history._",
        _section_overview(state),
    ]

    # Empty-state warning — happens when no PostToolUse hook fired (typical in
    # Cowork, which has a narrower hook surface than Claude Code). Without
    # recorded activity, this file can't summarise what you did — only what
    # the SessionStart hook captured at boot.
    if (state.current_turn == 0 and len(state.reads) == 0
            and len(state.edits) == 0 and len(state.bash_history) == 0):
        sections.append(
            "> **No session activity was recorded.** This usually means the "
            "PostToolUse hooks (Edit/Write/Bash/Read) did not fire — common "
            "in Cowork, which has a narrower hook surface than Claude Code. "
            "Install the plugin in Claude Code (terminal CLI) for full "
            "activity tracking + meaningful compaction. The scan engine and "
            "capsule generation still work in Cowork."
        )

    if narrative:
        sections.append(narrative)
    sections.append(_section_activity(state))
    sections.append(_section_consulted_files(state))
    sections.append(
        "## How to use this file\n\n"
        "Paste this entire file at the top of your next chat (or `/clear` "
        "and load via your skill flow). The next session will resume with "
        "the same context but a clean conversation buffer."
    )

    body = "\n\n".join(s for s in sections if s).strip() + "\n"

    meta = {
        "version": "0.9.0",
        "turn": state.current_turn,
        "session_id": state.session_id,
        "files_tracked": len(state.reads),
        "edits": len(state.edits),
        "bash": len(state.bash_history),
        "tokens_reclaimed_est": estimate_tokens_reclaimed(state),
        "llm_enhanced": bool(llm_meta),
        "llm": llm_meta,
    }
    return body, meta


def run_compact(
    project_root: str | Path,
    *,
    use_llm: bool = False,
    output_dir: str | Path | None = None,
) -> dict:
    """Top-level entry: load state, build working context, write the file."""
    project_root = Path(project_root).resolve()
    out_dir = Path(output_dir) if output_dir else project_root / "lensify-out"
    out_dir.mkdir(parents=True, exist_ok=True)

    state = load_state(project_root)
    body, meta = build_working_context(state, use_llm=use_llm)

    target = out_dir / "WORKING_CONTEXT.md"
    target.write_text(body, encoding="utf-8")
    meta["path"] = str(target)
    meta["size_bytes"] = len(body.encode("utf-8"))

    # Phase 7 — also persist a memory entry for cross-session recall
    memory_written = None
    if not memory_disabled():
        try:
            excerpt = body[:400]
            mem = memory_from_session_state(state, project_name=project_root.name, excerpt=excerpt)
            mem_path = save_memory(mem, project_root)
            if mem_path:
                memory_written = str(mem_path)
                if _record_event is not None:
                    try:
                        _record_event("memory_save", project_root=str(project_root))
                    except Exception:  # noqa: BLE001
                        pass
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"[lensify-memory] save failed: {exc}\n")
    meta["memory_written"] = memory_written

    # Phase 8 — record the compactor run with its token reclaim estimate
    if _record_event is not None:
        try:
            _record_event(
                "compactor",
                project_root=str(project_root),
                tokens_saved=int(meta.get("tokens_reclaimed_est", 0)),
            )
        except Exception:  # noqa: BLE001
            pass

    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lensify conversation compactor.")
    p.add_argument("target", help="Project path")
    p.add_argument("--llm", action="store_true",
                   help="Enhance with one Haiku call (requires ANTHROPIC_API_KEY)")
    p.add_argument("--json", action="store_true",
                   help="Emit only the metadata banner JSON on stdout")
    p.add_argument("--output", default=None, help="Override output directory")
    args = p.parse_args(argv)

    use_llm = args.llm or os.environ.get("LENSIFY_COMPACT_LLM") in ("1", "true", "yes", "on")
    try:
        meta = run_compact(args.target, use_llm=use_llm, output_dir=args.output)
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(meta, indent=2))
    else:
        print(json.dumps({
            "path": meta["path"],
            "tokens_reclaimed_est": meta["tokens_reclaimed_est"],
            "llm_enhanced": meta["llm_enhanced"],
        }))
        sys.stderr.write(
            f"Wrote {meta['path']} ({meta['size_bytes']} bytes). "
            f"Estimated tokens reclaimed: {meta['tokens_reclaimed_est']:,}.\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
