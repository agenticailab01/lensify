"""PostToolUse hook: compress large Bash / web-fetch outputs.

OPT-IN (default OFF). Enable with `LENSIFY_COMPRESS_OUTPUT=1`.

Honesty note: a PostToolUse hook *cannot* suppress the tool's raw output — the
agent has already received it. This hook only *appends* a summary via
additionalContext, so within a turn it is net-neutral-to-negative on tokens.
The only saving is downstream, *if* the session auto-compacts and the summary
is carried instead of the raw blob — which is not guaranteed. We therefore
default it OFF and count its savings as **potential**, not realized.

For a *realized* saving, use the `lensify run [--] <cmd>` wrapper instead: it
compresses before the output ever reaches the model.

When enabled and the tool's output exceeds MIN_COMPRESS_BYTES the hook:
    1. Stores the raw output on disk under `.lensify-outputs/<sha>.txt`
    2. Generates a per-type compressed summary
    3. Returns the summary + retrieval handle as additionalContext
    4. Records a compression event in session_state for telemetry

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
        compress, format_for_agent, MIN_COMPRESS_BYTES,
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


def _hook_enabled() -> bool:
    """Opt-in: the passive compression hook is OFF unless explicitly enabled.

    Enable with LENSIFY_COMPRESS_OUTPUT in {1,true,yes,on}. The global
    LENSIFY_DEDUP=0 kill-switch still disables it regardless.
    """
    if os.environ.get("LENSIFY_DEDUP", "1") in ("0", "false", "no", "off"):
        return False
    return os.environ.get("LENSIFY_COMPRESS_OUTPUT", "0") in ("1", "true", "yes", "on")


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
    if not _hook_enabled():
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
        sys.stderr.write(f"[lensify-compress] state update failed: {exc}\n")

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
        sys.stderr.write(f"[lensify-compress] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
