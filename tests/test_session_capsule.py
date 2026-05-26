"""Tests for the session_capsule builder."""
from __future__ import annotations

import pytest

from scripts.session_state import (
    SessionState, record_edit, record_bash, parse_test_output,
    record_test_result, check_and_record, increment_turn,
)
from scripts.session_capsule import (
    build_session_capsule, write_session_capsule, should_refresh, TOTAL_BUDGET,
)
from scripts.capsule import estimate_tokens


@pytest.fixture
def populated_state(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    state.current_turn = 5

    # Some reads
    for i in range(4):
        f = tmp_path / "src" / f"file_{i}.py"
        f.parent.mkdir(exist_ok=True)
        f.write_text(f"x = {i}\n")
        check_and_record(state, f, tmp_path)

    # Some edits
    for i in range(3):
        record_edit(state, tmp_path / "src" / f"file_{i}.py", tmp_path)

    # Bash + test
    record_bash(state, "pytest -q", exit_status=0)
    record_bash(state, "git status")
    tr = parse_test_output("==== 23 passed, 2 failed ====")
    record_test_result(state, tr)
    return state, tmp_path


def test_session_capsule_has_markers(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    assert "<!-- lensify-session-begin -->" in capsule
    assert "<!-- lensify-session-end -->" in capsule


def test_session_capsule_within_budget(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    tokens = estimate_tokens(capsule)
    assert tokens <= TOTAL_BUDGET * 1.15, f"capsule over budget: {tokens} > {TOTAL_BUDGET}"


def test_session_capsule_contains_header(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    assert "SESSION ACTIVITY" in capsule
    assert "Turn 5" in capsule


def test_session_capsule_contains_edits(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    assert "Recent edits" in capsule
    assert "file_0.py" in capsule or "file_1.py" in capsule


def test_session_capsule_contains_tests(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    assert "Last test run" in capsule
    assert "23 passed" in capsule or "23" in capsule


def test_session_capsule_contains_bash(populated_state):
    state, _ = populated_state
    capsule = build_session_capsule(state)
    assert "pytest -q" in capsule
    assert "git status" in capsule


def test_session_capsule_empty_state(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    capsule = build_session_capsule(state)
    # Should still produce something with header
    assert "SESSION ACTIVITY" in capsule
    assert "<!-- lensify-session-begin -->" in capsule


def test_write_session_capsule_writes_file(populated_state):
    state, project = populated_state
    path = write_session_capsule(state, project)
    assert path.exists()
    content = path.read_text()
    assert "SESSION ACTIVITY" in content


def test_should_refresh_at_intervals(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    # Need at least 3 reads
    for i in range(3):
        f = tmp_path / f"f_{i}.py"
        f.write_text("x=1\n")
        check_and_record(state, f, tmp_path)
    # Not a refresh turn
    state.current_turn = 3
    assert should_refresh(state, every=5) is False
    # Refresh turn
    state.current_turn = 5
    assert should_refresh(state, every=5) is True
    state.current_turn = 10
    assert should_refresh(state, every=5) is True


def test_should_refresh_skips_when_few_reads(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    state.current_turn = 5
    # Zero reads
    assert should_refresh(state, every=5) is False


def test_should_refresh_skips_turn_zero(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    assert should_refresh(state) is False
