"""PreToolUse / SessionStart hook entry point.

Reads a Claude Code hook payload from stdin, decides whether the file the
agent is about to Read has already been read in this session, and emits a
hook-specific output that adds a one-line `additionalContext` note.

Contract:
    - Exit 0 always (never block the read — we only advise the agent).
    - Stdout: JSON with hookSpecificOutput (or empty {} when nothing to add).
    - Stderr: optional diagnostics; ignored by Claude Code.

Invocation modes:
    python3 dedup_hook.py               # normal PreToolUse hook
    python3 dedup_hook.py --session-start   # SessionStart reset
    python3 dedup_hook.py --stats <path>    # print session stats (debug only)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running as a script — append the parent dir so `scripts.session_state` resolves.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from session_state import (
        check_and_record, increment_turn, load_state, reset_state,
        save_state, session_summary, is_disabled,
    )
    try:
        from stats import record_event as _record_event
    except ImportError:
        _record_event = None  # stats are optional
except ImportError:  # pragma: no cover — defensive
    print("{}")
    sys.exit(0)


def _emit(payload: dict) -> None:
    """Write JSON to stdout and exit 0."""
    try:
        json.dump(payload, sys.stdout)
    except (TypeError, ValueError):
        sys.stdout.write("{}")
    sys.stdout.write("\n")
    sys.stdout.flush()


def _project_root_from_payload(payload: dict) -> str:
    """Best-effort: extract project root from the hook payload."""
    # Claude Code passes `cwd` for most hook events; fall back to env / cwd.
    cwd = payload.get("cwd") or payload.get("working_directory")
    if cwd and os.path.isdir(cwd):
        return cwd
    env_cwd = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_cwd and os.path.isdir(env_cwd):
        return env_cwd
    return os.getcwd()


def handle_session_start(payload: dict) -> None:
    """Reset session state at the start of a new Claude session."""
    if is_disabled():
        _emit({})
        return
    root = _project_root_from_payload(payload)
    session_id = str(payload.get("session_id", ""))
    reset_state(root, session_id=session_id)
    _emit({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "ProjectLens dedup is active. Repeat file reads will be "
                "flagged in this session."
            ),
        }
    })


def handle_pre_tool_use(payload: dict) -> None:
    """Inspect a Read tool call; advise the agent if it's a duplicate."""
    if is_disabled():
        _emit({})
        return
    tool_name = payload.get("tool_name") or payload.get("tool")
    if tool_name != "Read":
        _emit({})
        return

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        _emit({})
        return

    root = _project_root_from_payload(payload)
    state = load_state(root)
    # Each PreToolUse on Read is a chance to detect that a new prompt has
    # arrived. We use a coarse heuristic: first Read after state load bumps
    # the turn counter. This isn't perfect (multiple Reads in one turn won't
    # all bump) — that's fine, we only need turn numbers for the agent's
    # context note.
    if not getattr(state, "_turn_bumped_this_load", False):
        increment_turn(state)
        state._turn_bumped_this_load = True  # type: ignore[attr-defined]

    decision = check_and_record(state, file_path, root)
    save_state(state, root)

    if not decision.is_duplicate:
        _emit({})
        return

    # Record lifetime telemetry (Phase 8) — never fail the hook on stats error
    if _record_event is not None:
        try:
            _record_event("dedup", project_root=root)
        except Exception:  # noqa: BLE001
            pass

    # Surface the dedup note to the agent
    _emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": decision.note,
        }
    })


def handle_stats(args: list[str]) -> None:
    """Print human-readable session stats to stdout for debugging."""
    root = args[0] if args else os.getcwd()
    state = load_state(root)
    summary = session_summary(state)
    print(json.dumps(summary, indent=2))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    if argv and argv[0] == "--session-start":
        # SessionStart hook may pass JSON on stdin too; tolerate either form.
        payload: dict = {}
        if not sys.stdin.isatty():
            try:
                raw = sys.stdin.read()
                if raw:
                    payload = json.loads(raw)
            except json.JSONDecodeError:
                pass
        handle_session_start(payload)
        return 0

    if argv and argv[0] == "--stats":
        handle_stats(argv[1:])
        return 0

    # Default: PreToolUse — read payload from stdin
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        _emit({})
        return 0

    try:
        handle_pre_tool_use(payload)
    except Exception as exc:  # noqa: BLE001 — never let the hook crash the read
        sys.stderr.write(f"[projectlens-dedup] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
