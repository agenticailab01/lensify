"""Tests for the PostToolUse activity hook (Phase 2)."""
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
    / "skills" / "lensify" / "scripts" / "activity_hook.py"
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


@pytest.fixture
def project(tmp_path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def f(): pass\n")
    return tmp_path


def test_hook_records_edit(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
        "tool_response": {},
    }
    run_hook(payload)
    state = load_state(project)
    assert len(state.edits) == 1
    assert state.edits[0].op == "edit"
    assert state.edits[0].rel_path == "src/main.py"


def test_hook_records_write(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Write",
        "tool_input": {"file_path": str(project / "src" / "new.py")},
        "tool_response": {},
    }
    run_hook(payload)
    state = load_state(project)
    assert len(state.edits) == 1
    assert state.edits[0].op == "write"


def test_hook_records_bash(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Bash",
        "tool_input": {"command": "pytest -q"},
        "tool_response": {"exit_code": 0, "stdout": "==== 5 passed ===="},
    }
    run_hook(payload)
    state = load_state(project)
    assert len(state.bash_history) == 1
    assert "pytest" in state.bash_history[0].command
    assert state.bash_history[0].exit_status == 0


def test_hook_parses_test_output(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Bash",
        "tool_input": {"command": "pytest"},
        "tool_response": {"exit_code": 1, "stdout": "==== 5 passed, 2 failed ===="},
    }
    run_hook(payload)
    state = load_state(project)
    assert state.last_test is not None
    assert state.last_test.passed == 5
    assert state.last_test.failed == 2


def test_hook_silent_for_unmatched_tools(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
        "tool_response": {},
    }
    out = run_hook(payload)
    # The activity hook ignores Read; output is empty
    assert "hookSpecificOutput" not in out


def test_hook_disabled_by_env(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(project / "src" / "main.py")},
        "tool_response": {},
    }
    run_hook(payload, env_extra={"LENSIFY_DEDUP": "0"})
    state = load_state(project)
    # No activity recorded since hook bailed
    assert len(state.edits) == 0


def test_hook_handles_missing_file_path_gracefully(project):
    payload = {
        "cwd": str(project),
        "tool_name": "Edit",
        "tool_input": {},
        "tool_response": {},
    }
    run_hook(payload)
    state = load_state(project)
    # No edit recorded (path missing) but no crash
    assert len(state.edits) == 0


def test_hook_handles_malformed_stdin():
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="this isn't JSON",
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0
