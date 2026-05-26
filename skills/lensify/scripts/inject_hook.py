"""UserPromptSubmit hook — selective capsule injection.

When the user submits a prompt, this hook:
    1. Loads lensify-out/lens.sections.json (if present)
    2. Picks 1-4 relevant sections based on the prompt's keywords/module-names
    3. Optionally appends SESSION.capsule.md content when the prompt indicates
       the user is asking about session activity
    4. Returns the selected content as additionalContext

Contract:
    - Exit 0 always
    - Stdout: empty when no lens / no match, or
              {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                      "additionalContext": "..." }}
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
    from section_matcher import match, cap, MAX_SECTIONS
    from session_state import is_disabled
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


def _load_sections(project_root: str) -> dict | None:
    """Load lens.sections.json from lensify-out/ if present."""
    p = Path(project_root) / "lensify-out" / "lens.sections.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_session_capsule(project_root: str) -> str:
    p = Path(project_root) / "lensify-out" / "SESSION.capsule.md"
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_prompt(payload: dict) -> str:
    """Try common keys Claude Code uses for the user's prompt."""
    for key in ("prompt", "user_prompt", "message", "user_message", "text"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
    # Some agents nest the prompt
    msg = payload.get("user", {})
    if isinstance(msg, dict):
        for key in ("content", "text", "message"):
            v = msg.get(key)
            if isinstance(v, str) and v:
                return v
    return ""


def handle(payload: dict) -> None:
    if is_disabled():
        _emit({})
        return

    prompt = _extract_prompt(payload)
    if not prompt or len(prompt.strip()) < 3:
        _emit({})
        return

    root = _project_root_from_payload(payload)
    lens = _load_sections(root)
    if not lens:
        _emit({})
        return

    sections_data = lens.get("sections", {})
    module_paths = lens.get("module_paths", []) or []
    symbol_names = lens.get("symbol_names", []) or []

    result = match(prompt, module_paths=module_paths, symbol_names=symbol_names)
    chosen = cap(result)
    if not chosen:
        _emit({})
        return

    # Compose the injected content
    parts: list[str] = []
    header = "[Lensify] Relevant context for your question:"
    parts.append(header)
    for name in chosen:
        body = sections_data.get(name)
        if body:
            parts.append(body)

    # If user is asking about session activity, append SESSION capsule too
    if result.needs_session:
        sess = _load_session_capsule(root)
        if sess:
            parts.append(sess)

    additional = "\n\n".join(parts).strip()
    if not additional:
        _emit({})
        return

    # Lifetime telemetry — selective injection saves vs. monolithic capsule
    if _record_event is not None:
        try:
            _record_event("selective_inject", project_root=root)
        except Exception:  # noqa: BLE001
            pass

    _emit({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
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
        sys.stderr.write(f"[lensify-inject] hook error: {exc}\n")
        _emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
