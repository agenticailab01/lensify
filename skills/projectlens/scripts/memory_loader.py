"""SessionStart hook: load relevant past-session memories.

This runs alongside (not instead of) the dedup_hook --session-start. Where the
dedup hook resets the within-session tracker, this hook surfaces context FROM
previous sessions in the same project — so the agent starts the new session
already knowing what was being worked on last time.

Retrieval logic (lightweight, no MCP, no vector DB):
    1. Read lens.sections.json if present — extract current module_paths.
    2. Walk .projectlens-memory/index.json.
    3. Score each memory by recency × module-overlap.
    4. Render the top-3 as additionalContext.

Contract:
    - Exit 0 always
    - Stdout: {} when nothing to recall, or hookSpecificOutput with the block.
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
    from memory import (
        recall_relevant, format_memories_for_injection, is_disabled as memory_disabled,
    )
    from session_state import is_disabled as dedup_disabled
    try:
        from stats import record_event as _record_event
    except ImportError:
        _record_event = None
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


def _current_module_paths(project_root: str) -> list[str]:
    """Load current module list from lens.sections.json if present."""
    path = Path(project_root) / "projectlens-out" / "lens.sections.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("module_paths", []) or [])
    except (OSError, json.JSONDecodeError):
        return []


def handle(payload: dict) -> None:
    if memory_disabled() or dedup_disabled():
        _emit({})
        return
    root = _project_root_from_payload(payload)
    modules = _current_module_paths(root)
    memories = recall_relevant(root, current_modules=modules)
    if not memories:
        _emit({})
        return
    block = format_memories_for_injection(memories)
    if not block:
        _emit({})
        return

    if _record_event is not None:
        try:
            _record_event("memory_recall", project_root=root)
        except Exception:  # noqa: BLE001
            pass

    _emit({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": block,
        }
    })


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
        sys.stderr.write(f"[projectlens-memory] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
