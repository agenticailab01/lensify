"""Tests for the Phase 8 lifetime telemetry module."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.stats import (
    LifetimeStats, load_stats, save_stats, reset_stats, record_event,
    statusline_short, stats_report, usd_saved,
    format_number, format_bytes, stats_path, stats_home,
    EVENT_TYPES, TOKENS_PER_DEDUPED_READ, BYTES_PER_TOKEN, is_disabled,
)


@pytest.fixture
def stats_dir(tmp_path, monkeypatch):
    """Redirect stats to an isolated tmp dir per test."""
    monkeypatch.setenv("PROJECTLENS_STATS_HOME", str(tmp_path))
    return tmp_path


# ----- Storage roundtrip -----

def test_load_returns_fresh_when_missing(stats_dir):
    s = load_stats()
    assert s.dedup_count == 0
    assert s.tokens_saved == 0
    assert s.compactor_runs == 0


def test_save_and_load_roundtrip(stats_dir):
    s = LifetimeStats(dedup_count=10, tokens_saved=3500, compactor_runs=2)
    save_stats(s)
    loaded = load_stats()
    assert loaded.dedup_count == 10
    assert loaded.tokens_saved == 3500
    assert loaded.compactor_runs == 2


def test_corrupted_file_recovers(stats_dir):
    (stats_dir / "stats.json").write_text("not json {{{")
    s = load_stats()
    assert s.dedup_count == 0


def test_partial_file_tolerated(stats_dir):
    """Old-format file missing fields should load with defaults."""
    (stats_dir / "stats.json").write_text(json.dumps({"dedup_count": 5}))
    s = load_stats()
    assert s.dedup_count == 5
    assert s.compactor_runs == 0


# ----- record_event -----

def test_record_dedup_adds_default_tokens(stats_dir):
    record_event("dedup")
    s = load_stats()
    assert s.dedup_count == 1
    assert s.tokens_saved == TOKENS_PER_DEDUPED_READ


def test_record_compression_converts_bytes_to_tokens(stats_dir):
    record_event("compression", bytes_saved=3500)
    s = load_stats()
    assert s.compressions == 1
    assert s.compress_bytes_saved == 3500
    # tokens_saved should be roughly bytes_saved / 3.5 = 1000
    assert s.tokens_saved == int(3500 / BYTES_PER_TOKEN)


def test_record_compactor_uses_provided_tokens(stats_dir):
    record_event("compactor", tokens_saved=17_400)
    s = load_stats()
    assert s.compactor_runs == 1
    assert s.tokens_saved == 17_400


def test_record_memory_recall_counts_only(stats_dir):
    record_event("memory_recall")
    s = load_stats()
    assert s.memory_recalls == 1
    assert s.tokens_saved == 0  # not measurable, no estimate


def test_record_selective_inject_default_estimate(stats_dir):
    record_event("selective_inject")
    s = load_stats()
    assert s.selective_injections == 1
    assert s.tokens_saved > 0


def test_record_scan_counts_only(stats_dir):
    record_event("scan")
    s = load_stats()
    assert s.scan_count == 1
    assert s.tokens_saved == 0


def test_record_unknown_event_silently_ignored(stats_dir):
    record_event("bogus_event")
    s = load_stats()
    assert s.dedup_count == 0
    assert s.tokens_saved == 0


def test_record_event_is_idempotent_on_failure(stats_dir, monkeypatch):
    """Even if save fails, record_event must never raise."""
    def bad_save(_):
        raise OSError("disk full")
    monkeypatch.setattr("scripts.stats.save_stats", bad_save)
    # Should not raise
    record_event("dedup")


def test_per_project_bucketing(stats_dir):
    record_event("dedup", project_root="/proj/a")
    record_event("dedup", project_root="/proj/a")
    record_event("dedup", project_root="/proj/b")
    s = load_stats()
    assert s.by_project["/proj/a"]["dedup_count"] == 2
    assert s.by_project["/proj/b"]["dedup_count"] == 1


def test_compression_bucketed_per_project(stats_dir):
    record_event("compression", project_root="/p", bytes_saved=5000)
    s = load_stats()
    assert s.by_project["/p"]["compressions"] == 1
    assert s.by_project["/p"]["tokens_saved"] > 0


# ----- Event types catalogue -----

def test_all_event_types_recognized(stats_dir):
    for evt in EVENT_TYPES:
        record_event(evt, bytes_saved=100, tokens_saved=50)
    s = load_stats()
    assert s.dedup_count >= 1
    assert s.compressions >= 1
    assert s.compactor_runs >= 1
    assert s.memory_recalls >= 1
    assert s.memory_saves >= 1
    assert s.selective_injections >= 1
    assert s.scan_count >= 1


# ----- Formatting -----

def test_format_number_compact():
    assert format_number(500) == "500"
    assert format_number(1500) == "1.5k"
    assert format_number(1_500_000) == "1.5M"
    assert format_number(1_000) == "1k"
    assert format_number(2_000_000) == "2M"


def test_format_bytes_compact():
    assert format_bytes(500) == "500B"
    assert format_bytes(2048) == "2KB"          # ".0KB" trimmed
    assert format_bytes(5_000_000) == "4.8MB"
    assert format_bytes(1024 * 1024) == "1MB"   # ".0MB" trimmed


def test_usd_saved_default_rate():
    # 1M tokens at $15/M
    assert usd_saved(1_000_000) == 15.0
    # 100k tokens
    assert abs(usd_saved(100_000) - 1.5) < 0.001


def test_usd_saved_env_override(monkeypatch):
    monkeypatch.setenv("PROJECTLENS_USD_PER_MTOK", "0.80")
    assert abs(usd_saved(1_000_000) - 0.80) < 0.001


def test_statusline_short_basic(stats_dir):
    record_event("dedup")
    record_event("dedup")
    record_event("compactor", tokens_saved=10_000)
    s = load_stats()
    line = statusline_short(s)
    assert line.startswith("[LENS]")
    assert "⛏" in line
    assert "k" in line  # 10k+ tokens formatted compactly


def test_statusline_short_dedup_compactor_counts(stats_dir):
    for _ in range(15):
        record_event("dedup")
    record_event("compactor", tokens_saved=5_000)
    s = load_stats()
    line = statusline_short(s)
    assert "15d" in line or "15 d" in line.replace("·", "")
    assert "1c" in line


def test_stats_report_includes_all_sections(stats_dir):
    record_event("dedup")
    record_event("compression", bytes_saved=5_000, project_root="/x")
    record_event("compactor", tokens_saved=12_000, project_root="/x")
    s = load_stats()
    report = stats_report(s)
    assert "Tokens saved" in report
    assert "Dedup hooks" in report
    assert "Compressions" in report
    assert "Compactor runs" in report
    assert "Top projects" in report


def test_stats_report_no_projects_section_when_empty(stats_dir):
    s = load_stats()
    report = stats_report(s)
    assert "Top projects" not in report


def test_reset_wipes_file(stats_dir):
    record_event("dedup")
    assert stats_path().exists()
    reset_stats()
    assert not stats_path().exists()


# ----- Opt-out -----

def test_is_disabled_default_false(monkeypatch):
    monkeypatch.delenv("PROJECTLENS_STATS", raising=False)
    assert is_disabled() is False


def test_is_disabled_via_env(monkeypatch):
    monkeypatch.setenv("PROJECTLENS_STATS", "0")
    assert is_disabled() is True


# ----- Concurrency safety (atomic write) -----

def test_atomic_writes_dont_corrupt(stats_dir):
    """Rapid sequential writes shouldn't leave a half-written file."""
    for i in range(20):
        record_event("dedup")
    s = load_stats()
    assert s.dedup_count == 20
