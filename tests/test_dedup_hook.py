"""Tests for the dedup hook entry point.

Simulates Claude Code's hook invocation by writing JSON to the script's stdin
and parsing JSON from stdout.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills" / "projectlens" / "scripts" / "dedup_hook.py"
)


def run_hook(payload: dict, args: list[str] | None = None, env_extra: dict | None = None) -> dict:
    """Run the hook as a subprocess and return its stdout JSON."""
    import os
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), *(args or [])],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


@pytest.fixture
def project(tmp_path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello(): pass\n")
    return tmp_path


def test_hook_silent_for_non_read_tool(project):
    out = run_hook({
        "cwd": str(project),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    })
    assert out == {} or "hookSpecificOutput" not in out


def test_hook_silent_on_first_read(project):
    out = run_hook({
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    })
    assert "hookSpecificOutput" not in out


def test_hook_flags_duplicate_read(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    }
    run_hook(payload)  # first
    out = run_hook(payload)  # second
    assert "hookSpecificOutput" in out
    note = out["hookSpecificOutput"]["additionalContext"]
    assert "DEDUP" in note
    assert "src/main.py" in note
    assert "already read" in note.lower()


def test_hook_flags_content_change_distinctly(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    }
    run_hook(payload)  # first read
    # Modify file
    (project / "src" / "main.py").write_text("def hello(): pass\n# changed\n")
    out = run_hook(payload)
    assert "hookSpecificOutput" in out
    note = out["hookSpecificOutput"]["additionalContext"]
    assert "changed" in note.lower()


def test_hook_handles_missing_file_path(project):
    out = run_hook({
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {},
    })
    # Should not crash; should emit empty
    assert out == {} or "hookSpecificOutput" not in out


def test_hook_handles_empty_stdin(project):
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    # Empty stdin yields empty output, no crash
    assert proc.stdout.strip() in ("{}", "")


def test_hook_handles_malformed_json(project):
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="this is not json {{",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() in ("{}", "")


def test_session_start_resets_state(project):
    # Read first
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    }
    run_hook(payload)
    run_hook(payload)  # would normally flag as duplicate

    # Now fire SessionStart with a fresh ID
    run_hook({"session_id": "fresh-session", "cwd": str(project)}, args=["--session-start"])

    # Next read should be silent (state was reset)
    out = run_hook(payload)
    assert "hookSpecificOutput" not in out


def test_session_start_yields_friendly_note(project):
    out = run_hook(
        {"session_id": "s1", "cwd": str(project)},
        args=["--session-start"],
    )
    assert "hookSpecificOutput" in out
    note = out["hookSpecificOutput"]["additionalContext"]
    assert "dedup" in note.lower()


def test_disabled_by_env(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    }
    out1 = run_hook(payload, env_extra={"PROJECTLENS_DEDUP": "0"})
    out2 = run_hook(payload, env_extra={"PROJECTLENS_DEDUP": "0"})
    # Both should be empty — dedup disabled
    assert "hookSpecificOutput" not in out1
    assert "hookSpecificOutput" not in out2


def test_stats_mode_prints_summary(project):
    # Generate some state
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
    }
    run_hook(payload)
    run_hook(payload)

    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), "--stats", str(project)],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0
    summary = json.loads(proc.stdout)
    assert summary["files_tracked"] >= 1
    assert summary["duplicates_alerted"] >= 1
