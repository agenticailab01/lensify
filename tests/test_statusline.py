"""Tests for the Phase 8 statusline + stats_cli scripts."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.stats import LifetimeStats, save_stats, record_event

STATUSLINE_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "lensify" / "skills" / "lensify" / "scripts" / "statusline.py"
)
CLI_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "lensify" / "skills" / "lensify" / "scripts" / "stats_cli.py"
)


def run(script: Path, args: list[str], env_extra: dict | None = None,
        stdin: str = "") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin, capture_output=True, text=True, env=env, timeout=10,
    )


@pytest.fixture
def stats_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LENSIFY_STATS_HOME", str(tmp_path))
    return tmp_path


def test_statusline_silent_on_fresh_install(stats_home):
    proc = run(STATUSLINE_SCRIPT, [],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    # No events recorded → no badge displayed
    assert proc.stdout.strip() == ""


def test_statusline_emits_badge_after_events(stats_home):
    record_event("dedup")
    record_event("dedup")
    record_event("compactor", tokens_saved=12_000)
    proc = run(STATUSLINE_SCRIPT, [],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    out = proc.stdout.strip()
    assert "[LENS]" in out
    assert "⛏" in out


def test_statusline_disabled_by_env(stats_home):
    record_event("dedup")
    proc = run(STATUSLINE_SCRIPT, [], env_extra={
        "LENSIFY_STATS_HOME": str(stats_home),
        "LENSIFY_STATS": "0",
    })
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_statusline_never_crashes_on_corrupted_stats(stats_home):
    (stats_home / "stats.json").write_text("garbage")
    proc = run(STATUSLINE_SCRIPT, [],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0


# ----- stats_cli -----

def test_cli_full_report(stats_home):
    record_event("dedup")
    record_event("compression", bytes_saved=3500)
    record_event("compactor", tokens_saved=8_000, project_root="/x")
    proc = run(CLI_SCRIPT, [],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    assert "Lensify" in proc.stdout
    assert "Tokens saved" in proc.stdout
    assert "Dedup hooks" in proc.stdout
    assert "Compactor runs" in proc.stdout


def test_cli_short_form(stats_home):
    record_event("dedup")
    proc = run(CLI_SCRIPT, ["--short"],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    assert "[LENS]" in proc.stdout


def test_cli_json_form(stats_home):
    record_event("dedup")
    record_event("compactor", tokens_saved=5_000)
    proc = run(CLI_SCRIPT, ["--json"],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["dedup_count"] == 1
    assert data["compactor_runs"] == 1
    assert "statusline_short" in data
    assert "usd_saved_est" in data


def test_cli_reset_with_yes(stats_home):
    record_event("dedup")
    proc = run(CLI_SCRIPT, ["--reset", "--yes"],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    assert "Wiped" in proc.stdout
    assert not (stats_home / "stats.json").exists()


def test_cli_path_prints_location(stats_home):
    proc = run(CLI_SCRIPT, ["--path"],
               env_extra={"LENSIFY_STATS_HOME": str(stats_home)})
    assert proc.returncode == 0
    assert str(stats_home) in proc.stdout
