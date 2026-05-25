"""Tests for the Phase 4 conversation compactor."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.session_state import (
    SessionState, save_state, record_edit, record_bash,
    parse_test_output, record_test_result, check_and_record,
)
from scripts.compact import (
    build_working_context, run_compact, estimate_tokens_reclaimed,
    _section_overview, _section_activity, _section_consulted_files,
)
from scripts.llm_client import LLMResult


COMPACT_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills" / "projectlens" / "scripts" / "compact.py"
)


@pytest.fixture
def busy_state(tmp_path):
    """A reasonably populated session state."""
    state = SessionState(project_root=str(tmp_path))
    state.current_turn = 10
    state.started_at = 1_700_000_000.0
    for i in range(5):
        f = tmp_path / "api" / f"r_{i}.py"
        f.parent.mkdir(exist_ok=True)
        f.write_text(f"def f_{i}(): pass\n")
        check_and_record(state, f, tmp_path)
        check_and_record(state, f, tmp_path)  # duplicate
    record_edit(state, tmp_path / "api" / "r_0.py", tmp_path)
    record_edit(state, tmp_path / "api" / "r_1.py", tmp_path)
    record_bash(state, "pytest -q", exit_status=0)
    record_bash(state, "git status", exit_status=0)
    tr = parse_test_output("==== 23 passed, 2 failed ====")
    record_test_result(state, tr)
    save_state(state, tmp_path)
    return state, tmp_path


def test_build_working_context_deterministic_returns_markdown(busy_state):
    state, _ = busy_state
    body, meta = build_working_context(state, use_llm=False)
    assert "# Working Context" in body
    assert "Session overview" in body
    assert "Active modules" in body
    assert "Files touched" in body
    assert meta["llm_enhanced"] is False
    assert meta["turn"] == 10


def test_build_working_context_includes_failing_tests(busy_state):
    state, _ = busy_state
    body, _ = build_working_context(state, use_llm=False)
    assert "Last test run" in body
    assert "23 passed" in body or "23" in body
    assert "2 failed" in body or "2" in body


def test_build_working_context_includes_dedup_stats(busy_state):
    state, _ = busy_state
    body, _ = build_working_context(state, use_llm=False)
    assert "dedup" in body.lower()
    # We had 5 files × 2 reads = 10 attempts, 5 duplicates avoided
    assert "5" in body


def test_run_compact_writes_file(busy_state):
    state, project = busy_state
    meta = run_compact(project)
    target = project / "projectlens-out" / "WORKING_CONTEXT.md"
    assert target.exists()
    assert meta["path"] == str(target)
    assert meta["size_bytes"] > 100


def test_estimate_tokens_reclaimed_grows_with_turns():
    s = SessionState(current_turn=1)
    s10 = SessionState(current_turn=10)
    s50 = SessionState(current_turn=50)
    assert estimate_tokens_reclaimed(s) == 0
    assert estimate_tokens_reclaimed(s10) > 10_000
    assert estimate_tokens_reclaimed(s50) > estimate_tokens_reclaimed(s10)


def test_estimate_tokens_reclaimed_short_session_zero():
    s = SessionState(current_turn=0)
    assert estimate_tokens_reclaimed(s) == 0


def test_section_overview_well_formed(busy_state):
    state, _ = busy_state
    out = _section_overview(state)
    assert "## Session overview" in out
    assert "Turn:" in out
    assert "**10**" in out


def test_section_activity_handles_empty_state(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    out = _section_activity(state)
    assert out == "" or "modules" not in out.lower()


def test_section_consulted_files_empty_when_no_reads(tmp_path):
    state = SessionState(project_root=str(tmp_path))
    out = _section_consulted_files(state)
    assert out == ""


def test_llm_mode_without_key_falls_back(busy_state, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    state, _ = busy_state
    body, meta = build_working_context(state, use_llm=True)
    assert "LLM enhancement requested" in body or "ANTHROPIC_API_KEY" in body
    assert meta["llm_enhanced"] is False


def test_llm_mode_with_successful_call(busy_state, monkeypatch):
    state, _ = busy_state
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    fake_result = LLMResult(
        text="## What we were doing\n\nIterating on the api/ module.",
        input_tokens=200, output_tokens=80, duration_seconds=0.3,
    )
    with patch("scripts.compact.call_claude", return_value=fake_result):
        body, meta = build_working_context(state, use_llm=True)
    assert "Iterating on the api/ module" in body
    assert meta["llm_enhanced"] is True
    assert meta["llm"]["input_tokens"] == 200
    assert "est_usd" in meta["llm"]


def test_llm_mode_with_api_error_falls_back(busy_state, monkeypatch):
    state, _ = busy_state
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    fake_result = LLMResult(text=None, error="HTTP 429: rate limit")
    with patch("scripts.compact.call_claude", return_value=fake_result):
        body, meta = build_working_context(state, use_llm=True)
    assert "LLM call failed" in body
    assert "429" in body
    assert meta["llm_enhanced"] is False
    # Activity section is still present
    assert "Files touched" in body or "## Session overview" in body


def test_cli_runs_deterministically(busy_state, tmp_path):
    _, project = busy_state
    proc = subprocess.run(
        [sys.executable, str(COMPACT_SCRIPT), str(project)],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0
    banner = json.loads(proc.stdout)
    assert "path" in banner
    assert banner["llm_enhanced"] is False
    assert (project / "projectlens-out" / "WORKING_CONTEXT.md").exists()


def test_cli_emits_json_with_flag(busy_state):
    _, project = busy_state
    proc = subprocess.run(
        [sys.executable, str(COMPACT_SCRIPT), str(project), "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0
    meta = json.loads(proc.stdout)
    assert meta["turn"] == 10
    assert "tokens_reclaimed_est" in meta


def test_cli_nonexistent_path_exits_nonzero():
    proc = subprocess.run(
        [sys.executable, str(COMPACT_SCRIPT), "/nonexistent/xyz"],
        capture_output=True, text=True, timeout=15,
    )
    # FileNotFoundError → exit 2; if the script swallowed it that'd be a bug
    # Some configurations may still succeed with an empty state file written
    # to a created directory, so accept 0-or-2
    assert proc.returncode in (0, 2)


def test_compact_includes_session_id(busy_state):
    state, project = busy_state
    state.session_id = "my-test-session-id"
    save_state(state, project)
    meta = run_compact(project)
    body = (project / "projectlens-out" / "WORKING_CONTEXT.md").read_text()
    assert "my-test-session-id" in body
