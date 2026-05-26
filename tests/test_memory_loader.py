"""Subprocess tests for the SessionStart memory loader hook."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.memory import save_memory, MemoryEntry

LOADER_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "lensify" / "skills" / "lensify" / "scripts" / "memory_loader.py"
)


def run_loader(payload: dict, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(LOADER_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=10,
    )
    assert proc.returncode == 0, f"loader exited {proc.returncode}: {proc.stderr}"
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def _make_memory(session_id="s1", modules=None, topics=None, saved_at=None) -> MemoryEntry:
    return MemoryEntry(
        session_id=session_id,
        saved_at=saved_at or time.time(),
        project_name="demo",
        started_at=(saved_at or time.time()) - 600,
        last_turn=5,
        duration_minutes=15,
        active_modules=modules or [],
        files_touched=[],
        last_test_summary=None,
        excerpt="working on the auth module",
        topics=topics or [],
    )


def test_loader_silent_with_no_memories(tmp_path):
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"})
    assert "hookSpecificOutput" not in out


def test_loader_injects_when_memories_exist(tmp_path):
    save_memory(_make_memory("past", modules=["api"], topics=["auth", "jwt"]), tmp_path)
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"})
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    assert "Memories from previous sessions" in text


def test_loader_uses_module_overlap_when_lens_present(tmp_path):
    # Save two memories
    save_memory(_make_memory("api_session", modules=["api"]), tmp_path)
    save_memory(_make_memory("unrelated", modules=["billing"]), tmp_path)
    # Write a sections file that says current modules are api/, domain/
    out_dir = tmp_path / "lensify-out"
    out_dir.mkdir()
    (out_dir / "lens.sections.json").write_text(json.dumps({
        "module_paths": ["api", "domain"],
        "sections": {},
    }))
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"})
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    # api_session should appear; billing-related may not
    assert "api" in text


def test_loader_disabled_by_env(tmp_path):
    save_memory(_make_memory("past", modules=["api"]), tmp_path)
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"},
                     env_extra={"LENSIFY_MEMORY": "0"})
    assert "hookSpecificOutput" not in out


def test_loader_disabled_by_global_dedup_env(tmp_path):
    save_memory(_make_memory("past", modules=["api"]), tmp_path)
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"},
                     env_extra={"LENSIFY_DEDUP": "0"})
    assert "hookSpecificOutput" not in out


def test_loader_handles_corrupted_sections_file(tmp_path):
    save_memory(_make_memory("past", modules=["api"]), tmp_path)
    out_dir = tmp_path / "lensify-out"
    out_dir.mkdir()
    (out_dir / "lens.sections.json").write_text("not json {{{")
    # Should still inject memory (uses pure recency since modules can't be loaded)
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"})
    assert "hookSpecificOutput" in out


def test_loader_malformed_stdin():
    proc = subprocess.run(
        [sys.executable, str(LOADER_SCRIPT)],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0


def test_loader_caps_at_max_recall(tmp_path):
    """Even if 10 memories match, the loader returns at most MAX_RECALL=3."""
    from scripts.memory import MAX_RECALL
    for i in range(10):
        save_memory(_make_memory(f"s_{i}", modules=["x"]), tmp_path)
    out = run_loader({"cwd": str(tmp_path), "session_id": "new"})
    text = out.get("hookSpecificOutput", {}).get("additionalContext", "")
    memory_blocks = text.count("### Memory")
    assert memory_blocks <= MAX_RECALL
