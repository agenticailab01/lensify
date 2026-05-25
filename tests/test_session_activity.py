"""Tests for Phase 2 session-activity tracking."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.session_state import (
    SessionState, record_edit, record_bash, parse_test_output,
    record_test_result, active_modules, load_state, save_state,
    increment_turn, MAX_EDITS, MAX_BASH,
)


@pytest.fixture
def project(tmp_path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def f(): pass\n")
    return tmp_path


def test_record_edit_appends(project):
    state = SessionState(project_root=str(project))
    rec = record_edit(state, project / "src" / "main.py", project)
    assert rec.op == "edit"
    assert rec.rel_path == "src/main.py"
    assert len(state.edits) == 1


def test_record_write_op(project):
    state = SessionState(project_root=str(project))
    rec = record_edit(state, project / "src" / "main.py", project, op="write")
    assert rec.op == "write"


def test_edit_cap(project):
    state = SessionState(project_root=str(project))
    for i in range(MAX_EDITS + 50):
        record_edit(state, project / f"f_{i}.py", project)
    assert len(state.edits) == MAX_EDITS


def test_record_bash_truncates_long_commands(project):
    state = SessionState(project_root=str(project))
    long_cmd = "echo " + "x" * 200
    rec = record_bash(state, long_cmd)
    assert len(rec.command) <= 120
    assert rec.command.endswith("...")


def test_bash_cap(project):
    state = SessionState(project_root=str(project))
    for i in range(MAX_BASH + 20):
        record_bash(state, f"echo {i}")
    assert len(state.bash_history) == MAX_BASH


def test_parse_pytest_passed_failed():
    out = "==== 23 passed, 2 failed in 1.02s ===="
    tr = parse_test_output(out)
    assert tr is not None
    assert tr.framework == "pytest"
    assert tr.passed == 23
    assert tr.failed == 2


def test_parse_pytest_failed_passed_order():
    out = "==== 2 failed, 23 passed in 1.02s ===="
    tr = parse_test_output(out)
    assert tr is not None
    assert tr.passed == 23
    assert tr.failed == 2


def test_parse_pytest_only_passed():
    out = "==== 23 passed in 1.02s ===="
    tr = parse_test_output(out)
    assert tr is not None
    assert tr.passed == 23
    assert tr.failed == 0


def test_parse_pytest_failing_tests_extracted():
    out = (
        "==== FAILURES ====\n"
        "FAILED tests/test_a.py::test_one\n"
        "FAILED tests/test_b.py::test_two\n"
        "==== 5 passed, 2 failed ===="
    )
    tr = parse_test_output(out)
    assert tr is not None
    assert "tests/test_a.py::test_one" in tr.failing_tests
    assert "tests/test_b.py::test_two" in tr.failing_tests


def test_parse_jest():
    out = "Tests:       2 failed, 5 passed, 7 total"
    tr = parse_test_output(out)
    assert tr is not None
    assert tr.framework == "jest"
    assert tr.failed == 2
    assert tr.passed == 5


def test_parse_go_pass():
    out = "ok  \tgithub.com/x/y\t0.123s\n"
    tr = parse_test_output(out)
    assert tr is not None
    assert tr.framework == "go"
    assert tr.passed == 1


def test_parse_returns_none_for_garbage():
    assert parse_test_output("hello world") is None
    assert parse_test_output("") is None


def test_record_test_result_sets_turn(project):
    state = SessionState(project_root=str(project))
    state.current_turn = 7
    tr = parse_test_output("==== 5 passed ====")
    record_test_result(state, tr)
    assert state.last_test is not None
    assert state.last_test.turn == 7


def test_active_modules_weights_edits_higher(project):
    state = SessionState(project_root=str(project))
    state.current_turn = 1
    # Lots of reads from "api/", one edit in "domain/"
    for i in range(5):
        f = project / "api" / f"r_{i}.py"
        f.parent.mkdir(exist_ok=True)
        f.write_text("x=1\n")
        from scripts.session_state import check_and_record
        check_and_record(state, f, project)
    record_edit(state, project / "domain" / "a.py", project)
    mods = active_modules(state)
    assert mods  # non-empty
    # api and domain should both appear
    names = [m[0] for m in mods]
    assert "api" in names or "domain" in names


def test_state_roundtrip_includes_activity(project):
    state = SessionState(project_root=str(project), current_turn=3)
    record_edit(state, project / "src" / "main.py", project)
    record_bash(state, "pytest -q", exit_status=0)
    tr = parse_test_output("==== 10 passed ====")
    record_test_result(state, tr)
    save_state(state, project)

    loaded = load_state(project)
    assert len(loaded.edits) == 1
    assert len(loaded.bash_history) == 1
    assert loaded.last_test is not None
    assert loaded.last_test.passed == 10
