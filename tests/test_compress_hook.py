"""Subprocess-style tests for the compress_hook (Phase 6)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.session_state import load_state

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills" / "lensify" / "scripts" / "compress_hook.py"
)


def run_hook(payload: dict, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=10,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def test_hook_silent_for_small_output(tmp_path):
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_response": {"stdout": "hi\n", "exit_code": 0},
    }
    assert "hookSpecificOutput" not in run_hook(payload)


def test_hook_silent_for_unmatched_tool(tmp_path):
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {"file_path": "/x"},
        "tool_response": {},
    }
    assert "hookSpecificOutput" not in run_hook(payload)


def test_hook_compresses_large_bash_output(tmp_path):
    # 5KB of JSON
    big = json.dumps({"items": [{"id": i, "name": "x" * 20} for i in range(200)]})
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "curl ..."},
        "tool_response": {"stdout": big, "exit_code": 0},
    }
    out = run_hook(payload)
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    assert "Lensify" in text
    assert "json" in text
    assert "ratio" in text.lower()


def test_hook_stores_raw_output_to_disk(tmp_path):
    big = "[role=button]\n" * 500
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "mcp__Claude_in_Chrome__get_page_text",
        "tool_input": {},
        "tool_response": {"content": big},
    }
    run_hook(payload)
    cache_dir = tmp_path / ".lensify-outputs"
    assert cache_dir.exists()
    files = list(cache_dir.glob("*.txt"))
    assert len(files) >= 1


def test_hook_records_event_in_session_state(tmp_path):
    big = "\n".join("INFO line " + str(i) for i in range(400))
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "tail -f log"},
        "tool_response": {"stdout": big, "exit_code": 0},
    }
    run_hook(payload)
    state = load_state(tmp_path)
    events = getattr(state, "compressions", None)
    assert events is not None
    assert len(events) >= 1
    e = events[-1]
    assert e["tool"] == "Bash"
    assert e["original_bytes"] >= len(big.encode("utf-8")) - 10


def test_hook_disabled_by_env(tmp_path):
    big = json.dumps({"x": "y" * 5000})
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "x"},
        "tool_response": {"stdout": big, "exit_code": 0},
    }
    out = run_hook(payload, env_extra={"LENSIFY_COMPRESS_OUTPUT": "0"})
    assert "hookSpecificOutput" not in out


def test_hook_handles_malformed_stdin():
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() in ("{}", "")


def test_hook_handles_missing_response(tmp_path):
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "x"},
        "tool_response": {},
    }
    out = run_hook(payload)
    assert "hookSpecificOutput" not in out


def test_hook_handles_list_content(tmp_path):
    """Some tools return content as a list of {type, text} dicts."""
    big_text = "x" * 5000
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "mcp__workspace__web_fetch",
        "tool_input": {"url": "https://example.com"},
        "tool_response": {"content": [{"type": "text", "text": big_text}]},
    }
    out = run_hook(payload)
    assert "hookSpecificOutput" in out
