"""Tests for the Phase 7 cross-session memory store."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.memory import (
    MemoryEntry, save_memory, load_memory, load_index, recall_relevant,
    extract_topics, memory_from_session_state, format_memories_for_injection,
    is_disabled, MEMORY_DIRNAME, INDEX_FILENAME, MAX_MEMORIES,
)
from scripts.session_state import (
    SessionState, record_edit, record_bash, parse_test_output,
    record_test_result, check_and_record,
)


@pytest.fixture
def project(tmp_path):
    return tmp_path


def _make_memory(session_id: str = "s1", saved_at: float | None = None,
                 modules: list[str] | None = None, topics: list[str] | None = None) -> MemoryEntry:
    return MemoryEntry(
        session_id=session_id,
        saved_at=saved_at or time.time(),
        project_name="demo",
        started_at=(saved_at or time.time()) - 3600,
        last_turn=10,
        duration_minutes=60,
        active_modules=modules or [],
        files_touched=[],
        last_test_summary=None,
        excerpt="iterating on auth flow",
        topics=topics or [],
    )


def test_save_creates_files(project):
    save_memory(_make_memory("s1"), project)
    mem_dir = project / MEMORY_DIRNAME
    assert mem_dir.exists()
    assert (mem_dir / INDEX_FILENAME).exists()
    files = list(mem_dir.glob("memory-*.json"))
    assert len(files) == 1


def test_save_updates_index(project):
    save_memory(_make_memory("s1"), project)
    save_memory(_make_memory("s2"), project)
    index = load_index(project)
    ids = {e["session_id"] for e in index}
    assert ids == {"s1", "s2"}


def test_save_replaces_existing_session_id(project):
    """Saving the same session_id twice should replace, not duplicate."""
    save_memory(_make_memory("dup"), project)
    save_memory(_make_memory("dup"), project)
    index = load_index(project)
    matches = [e for e in index if e["session_id"] == "dup"]
    assert len(matches) == 1


def test_load_memory_by_session_id(project):
    save_memory(_make_memory("findme", modules=["api", "domain"]), project)
    loaded = load_memory(project, "findme")
    assert loaded is not None
    assert loaded.session_id == "findme"
    assert "api" in loaded.active_modules


def test_load_memory_missing_returns_none(project):
    save_memory(_make_memory("s1"), project)
    assert load_memory(project, "nonexistent") is None


def test_recall_empty_when_no_memories(project):
    assert recall_relevant(project) == []


def test_recall_by_module_overlap(project):
    # Three memories with different modules
    save_memory(_make_memory("a", modules=["api"]), project)
    save_memory(_make_memory("b", modules=["domain"]), project)
    save_memory(_make_memory("c", modules=["unrelated"]), project)
    results = recall_relevant(project, current_modules=["api/v2", "domain"], top_k=3)
    ids = [r.session_id for r in results]
    # api and domain memories should rank highest
    assert "a" in ids
    assert "b" in ids
    # unrelated should rank lowest or be excluded
    if "c" in ids:
        assert ids.index("c") > ids.index("a")


def test_recall_recency_decay(project):
    # One recent + one old memory, same module
    now = time.time()
    save_memory(_make_memory("recent", saved_at=now - 3600, modules=["x"]), project)
    save_memory(_make_memory("old", saved_at=now - 30 * 86400, modules=["x"]), project)
    results = recall_relevant(project, current_modules=["x"], top_k=2)
    ids = [r.session_id for r in results]
    assert ids[0] == "recent"


def test_recall_pure_recency_when_no_current_modules(project):
    """With no current modules, fall back to pure recency."""
    save_memory(_make_memory("old", saved_at=time.time() - 86400 * 7), project)
    save_memory(_make_memory("new", saved_at=time.time()), project)
    results = recall_relevant(project, current_modules=None, top_k=2)
    ids = [r.session_id for r in results]
    assert ids[0] == "new"


def test_max_memories_enforced(project):
    """Beyond MAX_MEMORIES, oldest drop first."""
    for i in range(MAX_MEMORIES + 5):
        save_memory(_make_memory(f"s_{i}", saved_at=time.time() + i), project)
    index = load_index(project)
    assert len(index) == MAX_MEMORIES


def test_extract_topics_filters_stopwords():
    text = "the auth and the user authentication and the test"
    topics = extract_topics(text)
    # "the" is a stopword and "test" is in our stopword list
    assert "the" not in topics
    assert "test" not in topics


def test_extract_topics_returns_frequent_words():
    text = "authentication " * 5 + "middleware " * 3 + "ephemeral once"
    topics = extract_topics(text)
    assert "authentication" in topics
    assert "middleware" in topics


def test_extract_topics_empty():
    assert extract_topics("") == []


def test_memory_from_session_state(tmp_path):
    state = SessionState(session_id="test-id", current_turn=8,
                         started_at=time.time() - 30 * 60)
    state.project_root = str(tmp_path)
    # Build some activity
    for i in range(3):
        f = tmp_path / "api" / f"f_{i}.py"
        f.parent.mkdir(exist_ok=True)
        f.write_text("def x(): pass\n")
        check_and_record(state, f, tmp_path)
    record_edit(state, tmp_path / "api" / "f_0.py", tmp_path)
    record_bash(state, "pytest", exit_status=0)
    tr = parse_test_output("==== 5 passed ====")
    record_test_result(state, tr)
    mem = memory_from_session_state(state, project_name="myrepo", excerpt="we tested auth")
    assert mem.session_id == "test-id"
    assert mem.last_turn == 8
    assert "api" in mem.active_modules
    assert mem.last_test_summary
    assert "passed" in mem.last_test_summary.lower()
    assert mem.duration_minutes >= 29
    assert mem.excerpt == "we tested auth"


def test_format_memories_for_injection(project):
    save_memory(_make_memory("m1", modules=["api"], topics=["auth", "jwt"]), project)
    memories = recall_relevant(project, current_modules=["api"])
    block = format_memories_for_injection(memories)
    assert "Memories from previous sessions" in block
    assert "api" in block
    assert "auth" in block or "jwt" in block


def test_format_memories_empty():
    assert format_memories_for_injection([]) == ""


def test_is_disabled_default_false(monkeypatch):
    monkeypatch.delenv("LENSIFY_MEMORY", raising=False)
    assert is_disabled() is False


def test_is_disabled_via_env(monkeypatch):
    monkeypatch.setenv("LENSIFY_MEMORY", "0")
    assert is_disabled() is True


def test_save_no_op_when_disabled(project, monkeypatch):
    monkeypatch.setenv("LENSIFY_MEMORY", "0")
    result = save_memory(_make_memory("blocked"), project)
    assert result is None
    assert not (project / MEMORY_DIRNAME).exists()


def test_corrupted_index_recovers(project):
    save_memory(_make_memory("s1"), project)
    # Corrupt the index
    (project / MEMORY_DIRNAME / INDEX_FILENAME).write_text("not valid json")
    # Should not crash; new save should work
    save_memory(_make_memory("s2"), project)
    index = load_index(project)
    # Old index data is lost, but the new save succeeded
    assert isinstance(index, list)
    assert any(e["session_id"] == "s2" for e in index)


def test_memory_entry_roundtrip():
    e = _make_memory("rt", modules=["a", "b"], topics=["x", "y"])
    e.last_test_summary = "5 passed"
    d = e.to_dict()
    e2 = MemoryEntry.from_dict(d)
    assert e2.session_id == "rt"
    assert e2.active_modules == ["a", "b"]
    assert e2.last_test_summary == "5 passed"
