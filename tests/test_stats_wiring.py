"""Integration tests: verify each hook bumps lifetime stats correctly.

These confirm Phase 8 wiring across the existing Phase 1-7 hooks. Each test
runs the hook as a subprocess, then loads lifetime stats from an isolated
LENSIFY_STATS_HOME and checks that the right counters incremented.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.stats import load_stats

SCRIPTS = (
    Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify" / "scripts"
)


def run_hook(script_name: str, payload: dict, env_extra: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name)],
        input=json.dumps(payload), capture_output=True, text=True,
        env={**os.environ, **env_extra}, timeout=10,
    )


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "stats_home"
    monkeypatch.setenv("LENSIFY_STATS_HOME", str(home))
    return {"LENSIFY_STATS_HOME": str(home)}, home


def test_dedup_hook_bumps_dedup_count(env, tmp_path):
    env_extra, stats_home = env
    (tmp_path / "f.py").write_text("def x(): pass\n")
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "f.py")},
    }
    # First read — not a duplicate
    run_hook("dedup_hook.py", payload, env_extra)
    # Second read — should bump dedup
    run_hook("dedup_hook.py", payload, env_extra)
    # Stats home is set via the monkeypatch; load_stats picks it up
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.dedup_count >= 1
    assert s.tokens_saved > 0


def test_compress_hook_bumps_compression_count(env, tmp_path):
    env_extra, stats_home = env
    big = json.dumps({"items": [{"id": i} for i in range(300)]})
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "echo big"},
        "tool_response": {"stdout": big, "exit_code": 0},
    }
    run_hook("compress_hook.py", payload, env_extra)
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.compressions == 1
    assert s.tokens_saved > 0
    assert s.compress_bytes_saved > 0


def test_inject_hook_bumps_selective_injections(env, tmp_path):
    env_extra, stats_home = env
    out_dir = tmp_path / "lensify-out"
    out_dir.mkdir()
    (out_dir / "lens.sections.json").write_text(json.dumps({
        "module_paths": ["api"], "symbol_names": [],
        "sections": {"summary": "# SUMMARY\n\nA demo project."},
    }))
    payload = {"cwd": str(tmp_path), "prompt": "what is this project?"}
    run_hook("inject_hook.py", payload, env_extra)
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.selective_injections == 1


def test_memory_loader_bumps_memory_recalls(env, tmp_path):
    env_extra, stats_home = env
    # Pre-populate a memory
    from scripts.memory import save_memory, MemoryEntry
    import time as _time
    save_memory(MemoryEntry(
        session_id="prior", saved_at=_time.time() - 3600,
        project_name="x", started_at=_time.time() - 7200,
        last_turn=5, duration_minutes=15,
        active_modules=["api"], files_touched=["api/x.py"],
        excerpt="prior session", topics=["auth"],
    ), tmp_path)
    payload = {"cwd": str(tmp_path), "session_id": "new"}
    run_hook("memory_loader.py", payload, env_extra)
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.memory_recalls == 1


def test_dedup_no_count_on_first_read(env, tmp_path):
    """Non-duplicate reads must NOT bump the dedup counter."""
    env_extra, stats_home = env
    (tmp_path / "z.py").write_text("def y(): pass\n")
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "z.py")},
    }
    run_hook("dedup_hook.py", payload, env_extra)
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.dedup_count == 0


def test_compress_skipped_for_small_output(env, tmp_path):
    env_extra, stats_home = env
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_response": {"stdout": "hi\n", "exit_code": 0},
    }
    run_hook("compress_hook.py", payload, env_extra)
    os.environ["LENSIFY_STATS_HOME"] = str(stats_home)
    s = load_stats()
    assert s.compressions == 0


def test_stats_disabled_by_env_blocks_writes(env, tmp_path):
    """With LENSIFY_STATS=0 the hook should still run but not write stats.

    Note: the dedup hook still writes session state — only the stats file
    is suppressed. We verify by checking ~/.lensify/stats.json never
    appears.
    """
    env_extra, stats_home = env
    env_extra = {**env_extra, "LENSIFY_STATS": "0"}
    (tmp_path / "f.py").write_text("def x(): pass\n")
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "f.py")},
    }
    run_hook("dedup_hook.py", payload, env_extra)
    run_hook("dedup_hook.py", payload, env_extra)
    # The stats file may or may not exist; if it does, it should be zeroed
    # (because record_event short-circuits on is_disabled)
    # Note: stats.py is_disabled checks env at call time, so the bump is skipped.
    stats_file = stats_home / "stats.json"
    if stats_file.exists():
        data = json.loads(stats_file.read_text())
        # Should be empty / no dedup events
        assert int(data.get("dedup_count", 0)) == 0
