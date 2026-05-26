"""PostToolUse activity hook.

Records Edit / Write / Bash tool invocations into the session state, parses
test output when present, and triggers a session-capsule refresh every N turns.

Contract:
    - Exit 0 always
    - Stdout: empty or {"hookSpecificOutput": {...}} when something useful to surface
    - Stderr: optional diagnostics
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from session_state import (
        load_state, save_state, record_edit, record_bash,
        parse_test_output, record_test_result, is_disabled,
    )
    from session_capsule import (
        build_session_capsule, write_session_capsule, should_refresh,
    )
except ImportError:  # pragma: no cover
    print("{}")
    sys.exit(0)


def _emit(payload: dict) -> None:
    try:
        json.dump(payload, sys.stdout)
    except (TypeError, ValueError):
        sys.stdout.write("{}")
    sys.stdout.write("\n")
    sys.stdout.flush()


def _project_root_from_payload(payload: dict) -> str:
    cwd = payload.get("cwd") or payload.get("working_directory")
    if cwd and os.path.isdir(cwd):
        return cwd
    env_cwd = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_cwd and os.path.isdir(env_cwd):
        return env_cwd
    return os.getcwd()


def _extract_bash_output(payload: dict) -> tuple[str, int | None]:
    """Best-effort extraction of bash stdout/stderr and exit code from
    Claude Code's PostToolUse payload."""
    response = payload.get("tool_response") or payload.get("response") or {}
    out_parts = []
    for key in ("stdout", "output", "result"):
        v = response.get(key)
        if isinstance(v, str):
            out_parts.append(v)
    stderr = response.get("stderr")
    if isinstance(stderr, str):
        out_parts.append(stderr)
    exit_code = response.get("exit_code")
    if exit_code is None:
        exit_code = response.get("returncode")
    try:
        exit_code = int(exit_code) if exit_code is not None else None
    except (TypeError, ValueError):
        exit_code = None
    return ("\n".join(out_parts), exit_code)


def handle(payload: dict) -> None:
    if is_disabled():
        _emit({})
        return

    tool = payload.get("tool_name") or payload.get("tool")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not tool:
        _emit({})
        return

    root = _project_root_from_payload(payload)
    state = load_state(root)

    # ----- Edit / Write tracking -----
    if tool in ("Edit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
        if path:
            op = "write" if tool == "Write" else "edit"
            record_edit(state, path, root, op=op)

    # ----- Bash tracking + test detection -----
    elif tool == "Bash":
        cmd = tool_input.get("command") or ""
        output_text, exit_code = _extract_bash_output(payload)
        if cmd:
            record_bash(state, cmd, exit_status=exit_code)
        if output_text:
            tr = parse_test_output(output_text)
            if tr is not None:
                record_test_result(state, tr)

    # ----- Refresh session capsule periodically -----
    refreshed = False
    if should_refresh(state):
        try:
            write_session_capsule(state, root)
            refreshed = True
        except OSError:
            pass

    save_state(state, root)

    # Surface an unobtrusive note only when we just refreshed
    if refreshed:
        _emit({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "Lensify refreshed lensify-out/SESSION.capsule.md "
                    "to reflect current session activity."
                ),
            }
        })
    else:
        _emit({})


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        _emit({})
        return 0
    try:
        handle(payload)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[lensify-activity] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
