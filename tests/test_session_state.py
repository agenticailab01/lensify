"""Tests for the in-session state module."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.session_state import (
    SessionState, ReadRecord, STATE_FILENAME, STATE_VERSION, MAX_TRACKED_READS,
    load_state, save_state, reset_state, check_and_record, increment_turn,
    compute_hash, to_relative, session_summary, is_disabled,
)


@pytest.fixture
def project(tmp_path) -> Path:
    """Build a minimal project root with a single Python file."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    print('hi')\n")
    return tmp_path


def test_load_state_returns_fresh_when_missing(project):
    state = load_state(project)
    assert state.current_turn == 0
    assert state.reads == {}
    assert state.version == STATE_VERSION


def test_save_and_load_roundtrip(project):
    state = SessionState(
        session_id="s1", project_root=str(project), current_turn=3,
    )
    state.reads["/some/file.py"] = ReadRecord(
        rel_path="src/file.py", abs_path="/some/file.py",
        content_hash="abc", first_turn=1, last_turn=2, read_count=2,
    )
    save_state(state, project)
    loaded = load_state(project)
    assert loaded.session_id == "s1"
    assert loaded.current_turn == 3
    assert "/some/file.py" in loaded.reads
    assert loaded.reads["/some/file.py"].content_hash == "abc"


def test_load_state_corrupted_recovers(project):
    """A garbage state file should reset to fresh, never crash."""
    (project / STATE_FILENAME).write_text("not valid json {{{")
    state = load_state(project)
    assert state.current_turn == 0
    assert state.reads == {}


def test_first_read_is_not_duplicate(project):
    state = load_state(project)
    increment_turn(state)
    decision = check_and_record(state, project / "src" / "main.py", project)
    assert decision.is_duplicate is False
    assert decision.previous_record is None
    assert decision.new_record.read_count == 1


def test_second_read_same_content_is_duplicate(project):
    state = load_state(project)
    increment_turn(state)
    check_and_record(state, project / "src" / "main.py", project)
    increment_turn(state)
    decision = check_and_record(state, project / "src" / "main.py", project)
    assert decision.is_duplicate is True
    assert decision.is_modified is False
    assert decision.previous_record is not None
    assert "already read" in decision.note.lower()
    assert decision.new_record.read_count == 2


def test_read_after_content_change_flagged_as_modified(project):
    state = load_state(project)
    file = project / "src" / "main.py"
    increment_turn(state)
    check_and_record(state, file, project)
    # Modify the file
    file.write_text("# entirely different content\n" * 5)
    increment_turn(state)
    decision = check_and_record(state, file, project)
    assert decision.is_duplicate is True
    assert decision.is_modified is True
    assert "changed" in decision.note.lower()


def test_compute_hash_deterministic(project):
    file = project / "src" / "main.py"
    h1 = compute_hash(file)
    h2 = compute_hash(file)
    assert h1 == h2
    assert len(h1) > 0


def test_compute_hash_returns_none_for_missing():
    assert compute_hash("/no/such/file") is None


def test_to_relative_inside_project(project):
    rel = to_relative(project / "src" / "main.py", project)
    assert rel == "src/main.py"


def test_to_relative_outside_project_falls_back(project):
    rel = to_relative("/etc/hosts", project)
    assert rel == "/etc/hosts"  # absolute fallback


def test_reset_state_starts_fresh(project):
    # Populate
    state = load_state(project)
    increment_turn(state)
    check_and_record(state, project / "src" / "main.py", project)
    save_state(state, project)
    # Reset
    new_state = reset_state(project, session_id="brand-new")
    assert new_state.session_id == "brand-new"
    assert new_state.current_turn == 0
    assert new_state.reads == {}


def test_session_summary_counts_correctly(project):
    state = load_state(project)
    increment_turn(state)
    check_and_record(state, project / "src" / "main.py", project)
    check_and_record(state, project / "src" / "main.py", project)
    check_and_record(state, project / "src" / "main.py", project)
    summary = session_summary(state)
    assert summary["files_tracked"] == 1
    assert summary["total_read_attempts"] == 3
    assert summary["duplicates_alerted"] == 2


def test_cap_enforced(tmp_path):
    """Once we hit MAX_TRACKED_READS, oldest entries drop first."""
    state = SessionState(project_root=str(tmp_path))
    # Insert MAX + 5 fake records
    for i in range(MAX_TRACKED_READS + 5):
        f = tmp_path / f"f_{i}.py"
        f.write_text(f"x = {i}\n")
        increment_turn(state)
        check_and_record(state, f, tmp_path)
    assert len(state.reads) == MAX_TRACKED_READS


def test_increment_turn_advances():
    state = SessionState()
    assert state.current_turn == 0
    increment_turn(state)
    assert state.current_turn == 1
    increment_turn(state)
    assert state.current_turn == 2


def test_is_disabled_default_false(monkeypatch):
    monkeypatch.delenv("LENSIFY_DEDUP", raising=False)
    assert is_disabled() is False


@pytest.mark.parametrize("value", ["0", "false", "no", "off"])
def test_is_disabled_recognises_falsy(monkeypatch, value):
    monkeypatch.setenv("LENSIFY_DEDUP", value)
    assert is_disabled() is True


def test_atomic_write_no_partial_state_on_concurrent(project):
    """Two saves in quick succession should both produce valid JSON."""
    s1 = SessionState(session_id="a", current_turn=1)
    s2 = SessionState(session_id="b", current_turn=2)
    save_state(s1, project)
    save_state(s2, project)
    final = load_state(project)
    # last-write-wins; either way the file should parse
    assert final.session_id in ("a", "b")


def test_state_file_lives_in_project_root(project):
    state = SessionState()
    save_state(state, project)
    assert (project / STATE_FILENAME).exists()
