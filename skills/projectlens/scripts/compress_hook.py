"""PostToolUse hook: compress large Bash / web-fetch outputs.

Fires after Bash, WebFetch, or any tool that produces large textual results.
When the tool's output exceeds MIN_COMPRESS_BYTES the hook:

    1. Stores the raw output on disk under `.projectlens-outputs/<sha>.txt`
    2. Generates a per-type compressed summary
    3. Returns the summary + retrieval handle as additionalContext
    4. Records a compression event in session_state for telemetry

The original tool response is still seen by the agent (hooks cannot suppress
it), but the agent now has a much shorter structured form to refer to in
subsequent turns. Sessions auto-compact later carry forward our summary,
not the raw blob — that's where the real downstream savings land.

Contract:
    - Exit 0 always
    - Stdout: {} when nothing to do, or {hookSpecificOutput: {additionalContext: ...}}
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
    from output_compressor import (
        compress, format_for_agent, is_disabled, MIN_COMPRESS_BYTES,
    )
    from session_state import load_state, save_state
    try:
        from stats import record_event as _record_event
    except ImportError:
        _record_event = None
except ImportError:  # pragma: no cover
    print("{}")
    sys.exit(0)


# Tool names this hook will compress. Matches both core Claude Code tools and
# common MCP-namespaced web-fetch variants.
COMPRESSABLE_TOOLS = {
    "Bash",
    "WebFetch",
    "mcp__workspace__web_fetch",
    "mcp__claude_in_chrome__get_page_text",
    "mcp__Claude_in_Chrome__get_page_text",
}


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


def _extract_output_text(response: dict) -> str:
    """Pull a textual output blob from the tool_response payload."""
    parts: list[str] = []
    for key in ("stdout", "output", "result", "content", "text", "body"):
        v = response.get(key)
        if isinstance(v, str) and v:
            parts.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    inner = item.get("text") or item.get("content")
                    if isinstance(inner, str):
                        parts.append(inner)
                elif isinstance(item, str):
                    parts.append(item)
    return "\n".join(parts)


def handle(payload: dict) -> None:
    if is_disabled():
        _emit({})
        return

    tool = payload.get("tool_name") or payload.get("tool")
    if tool not in COMPRESSABLE_TOOLS:
        _emit({})
        return

    response = payload.get("tool_response") or payload.get("response") or {}
    text = _extract_output_text(response)
    if not text or len(text.encode("utf-8")) < MIN_COMPRESS_BYTES:
        _emit({})
        return

    root = _project_root_from_payload(payload)
    result = compress(text, project_root=root, store=True)

    # Record compression event in session state for telemetry / session capsule
    try:
        state = load_state(root)
        state.compressions.append({
            "turn": state.current_turn,
            "tool": tool,
            "original_bytes": result.original_bytes,
            "compressed_bytes": result.compressed_bytes,
            "output_type": result.output_type,
            "bytes_saved": result.bytes_saved,
        })
        # Cap to 100 events
        if len(state.compressions) > 100:
            state.compressions = state.compressions[-100:]
        save_state(state, root)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[projectlens-compress] state update failed: {exc}\n")

    additional = format_for_agent(result)
    if not additional:
        _emit({})
        return

    # Lifetime telemetry — record bytes saved and event count
    if _record_event is not None:
        try:
            _record_event("compression", project_root=root,
                          bytes_saved=result.bytes_saved)
        except Exception:  # noqa: BLE001
            pass

    _emit({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional,
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
        sys.stderr.write(f"[projectlens-compress] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
