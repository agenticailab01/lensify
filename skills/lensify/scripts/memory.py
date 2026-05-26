"""Cross-session memory store (Phase 7).

Persists session summaries between Claude sessions so that what was learned
in one session can be loaded back at the start of the next. Lightweight:
project-local JSON files, no MCP server, no SQLite, no vector store.

Storage layout::

    <project>/.lensify-memory/
        index.json                       # lightweight catalog
        memory-<session_id>.json         # one file per past session

Each memory file contains:
    - Session metadata (id, started_at, duration, turn count)
    - Top-N active modules
    - Files touched (last 10)
    - Last test result (if any)
    - Brief excerpt from the session's WORKING_CONTEXT.md
    - Top topics (extracted keywords from edits + commands)

Retrieval at SessionStart picks up to MAX_RECALL memories ranked by:
    score = recency_decay × 0.5 + module_overlap × 1.0

This is deliberately simple — no embeddings, no MCP, no external deps. The
goal is closing the Claude-Mem gap with the SMALLEST possible install
footprint. Heavyweight users still go to Claude-Mem; users who want
zero-friction get this.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

MEMORY_DIRNAME = ".lensify-memory"
INDEX_FILENAME = "index.json"
MAX_MEMORIES = 50           # keep at most this many; oldest dropped
MAX_RECALL = 3              # how many memories to inject at SessionStart
HALF_LIFE_DAYS = 14.0       # recency decay half-life


@dataclass
class MemoryEntry:
    """One persisted memory of a past session."""
    session_id: str
    saved_at: float                                # unix seconds
    project_name: str
    started_at: float
    last_turn: int
    duration_minutes: int
    active_modules: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)
    last_test_summary: str | None = None
    excerpt: str = ""                              # short prose excerpt (<= 400 chars)
    topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            session_id=str(data.get("session_id", "")),
            saved_at=float(data.get("saved_at", time.time())),
            project_name=str(data.get("project_name", "")),
            started_at=float(data.get("started_at", 0.0)),
            last_turn=int(data.get("last_turn", 0)),
            duration_minutes=int(data.get("duration_minutes", 0)),
            active_modules=list(data.get("active_modules", []) or []),
            files_touched=list(data.get("files_touched", []) or []),
            last_test_summary=data.get("last_test_summary"),
            excerpt=str(data.get("excerpt", "")),
            topics=list(data.get("topics", []) or []),
        )


def is_disabled() -> bool:
    """Opt out via LENSIFY_MEMORY=0."""
    val = os.environ.get("LENSIFY_MEMORY")
    return val in ("0", "false", "no", "off")


def _memory_dir(project_root: str | Path) -> Path:
    return Path(project_root) / MEMORY_DIRNAME


def _atomic_write_json(path: Path, data: dict | list) -> None:
    """Atomic write via temp + rename. Never raises."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False,
            dir=str(path.parent), prefix=".pl-mem-", suffix=".tmp",
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, path)
    except OSError as exc:
        # Best-effort; surface to stderr only
        import sys
        sys.stderr.write(f"[lensify-memory] write failed: {exc}\n")


def save_memory(entry: MemoryEntry, project_root: str | Path) -> Path | None:
    """Write the memory entry to disk and update the index."""
    if is_disabled():
        return None
    root = Path(project_root)
    mem_dir = _memory_dir(root)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", entry.session_id or f"sess-{int(entry.saved_at)}")
    target = mem_dir / f"memory-{safe_id}.json"
    _atomic_write_json(target, entry.to_dict())

    # Update index
    index = load_index(root)
    # Remove any prior entry for this session_id
    index = [e for e in index if e.get("session_id") != entry.session_id]
    index.append({
        "session_id": entry.session_id,
        "saved_at": entry.saved_at,
        "last_turn": entry.last_turn,
        "active_modules": entry.active_modules,
        "topics": entry.topics,
        "file": target.name,
    })
    # Enforce cap — drop oldest
    index.sort(key=lambda e: float(e.get("saved_at", 0)), reverse=True)
    if len(index) > MAX_MEMORIES:
        dropped = index[MAX_MEMORIES:]
        index = index[:MAX_MEMORIES]
        # Also delete the file backing each dropped index entry
        for d in dropped:
            try:
                (mem_dir / d.get("file", "")).unlink(missing_ok=True)
            except OSError:
                pass
    _atomic_write_json(mem_dir / INDEX_FILENAME, index)
    return target


def load_index(project_root: str | Path) -> list[dict]:
    """Return the index list, or [] if missing/corrupt."""
    path = _memory_dir(project_root) / INDEX_FILENAME
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError):
        return []
    return []


def load_memory(project_root: str | Path, session_id: str) -> MemoryEntry | None:
    """Look up a single memory entry by session_id."""
    mem_dir = _memory_dir(project_root)
    for f in mem_dir.glob("memory-*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("session_id") == session_id:
                return MemoryEntry.from_dict(data)
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _recency_score(saved_at: float, now: float | None = None) -> float:
    """Exponential decay with HALF_LIFE_DAYS."""
    now = now if now is not None else time.time()
    age_days = max(0.0, (now - saved_at) / 86_400.0)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def _overlap_score(memory_modules: list[str], current_modules: list[str]) -> float:
    """Fraction of current modules that overlap with the memory's modules."""
    if not current_modules:
        return 0.0
    cur = {m.split("/")[0].lower() for m in current_modules if m}
    mem = {m.split("/")[0].lower() for m in memory_modules if m}
    if not cur or not mem:
        return 0.0
    return len(cur & mem) / len(cur)


def recall_relevant(
    project_root: str | Path,
    current_modules: list[str] | None = None,
    top_k: int = MAX_RECALL,
) -> list[MemoryEntry]:
    """Return the top-K memories ranked by recency × module-overlap."""
    if is_disabled():
        return []
    index = load_index(project_root)
    if not index:
        return []
    now = time.time()
    scored: list[tuple[float, dict]] = []
    for entry in index:
        recency = _recency_score(float(entry.get("saved_at", 0)), now)
        overlap = _overlap_score(entry.get("active_modules", []) or [], current_modules or [])
        score = recency * 0.5 + overlap * 1.0
        # Boost if no current modules provided (use pure recency)
        if not current_modules:
            score = recency
        scored.append((score, entry))
    scored.sort(key=lambda kv: kv[0], reverse=True)
    out: list[MemoryEntry] = []
    for score, entry in scored[:top_k]:
        if score <= 0:
            continue
        # Skip very-low overlap when overlap was the dominant signal
        mem = _hydrate(project_root, entry)
        if mem:
            out.append(mem)
    return out


def _hydrate(project_root: str | Path, index_entry: dict) -> MemoryEntry | None:
    """Load the full MemoryEntry from disk given an index row."""
    path = _memory_dir(project_root) / str(index_entry.get("file", ""))
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return MemoryEntry.from_dict(data)
    except (OSError, json.JSONDecodeError):
        return None


# ----- Topic extraction (deterministic — no LLM) -----

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "into", "this", "that", "have", "has",
    "was", "are", "but", "all", "not", "you", "can", "will", "use", "using",
    "test", "tests", "file", "files", "code", "function", "class",
})


def extract_topics(text: str, top_n: int = 8) -> list[str]:
    """Pull frequent meaningful words from a body of text (edits/commands/excerpt)."""
    if not text:
        return []
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text.lower())
    counts: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS or len(w) < 4:
            continue
        counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]]


# ----- Rendering for SessionStart injection -----

def format_memories_for_injection(memories: list[MemoryEntry]) -> str:
    """Render up to top_k memories as a single additionalContext block."""
    if not memories:
        return ""
    lines = ["[Lensify] Memories from previous sessions in this project:"]
    for i, m in enumerate(memories, 1):
        when = _humanize_age(time.time() - m.saved_at)
        lines.append("")
        lines.append(f"### Memory {i} — {when}, turn {m.last_turn}, ~{m.duration_minutes} min")
        if m.active_modules:
            lines.append(f"- Active modules: {', '.join(f'`{m_}`' for m_ in m.active_modules[:5])}")
        if m.files_touched:
            lines.append(f"- Files touched: {', '.join(f'`{f}`' for f in m.files_touched[:5])}")
        if m.last_test_summary:
            lines.append(f"- Last test: {m.last_test_summary}")
        if m.topics:
            lines.append(f"- Topics: {', '.join(m.topics[:6])}")
        if m.excerpt:
            lines.append(f"- Excerpt: {m.excerpt[:300]}")
    lines.append("")
    lines.append("These are advisory hints — re-read files as needed, but consider this prior context when answering.")
    return "\n".join(lines)


def _humanize_age(seconds: float) -> str:
    if seconds < 3600:
        return f"{int(seconds / 60)} min ago"
    if seconds < 86_400:
        return f"{int(seconds / 3600)} hours ago"
    days = seconds / 86_400
    if days < 14:
        return f"{int(days)} day(s) ago"
    return f"{int(days / 7)} week(s) ago"


# ----- Build a memory from a SessionState -----

def memory_from_session_state(state, project_name: str = "", excerpt: str = "") -> MemoryEntry:
    """Construct a MemoryEntry from a SessionState — used by the compactor."""
    # Active modules (top-5 names only)
    try:
        from session_state import active_modules
    except ImportError:
        try:
            from .session_state import active_modules
        except ImportError:
            active_modules = lambda s, top_n=5: []  # type: ignore
    mods = [name for name, _ in active_modules(state, top_n=5)]
    files = [e.rel_path for e in state.edits[-10:]] if hasattr(state, "edits") else []
    last_test = None
    if getattr(state, "last_test", None):
        t = state.last_test
        if t.failed > 0:
            last_test = f"{t.framework}: {t.failed} failed, {t.passed} passed"
        else:
            last_test = f"{t.framework}: {t.passed} passed"
    duration = int(max(0, (time.time() - state.started_at) / 60))

    # Build topics from edits + bash + excerpt
    topic_source = " ".join([
        " ".join(e.rel_path for e in getattr(state, "edits", []) or []),
        " ".join(b.command for b in getattr(state, "bash_history", []) or []),
        excerpt,
    ])
    topics = extract_topics(topic_source)

    return MemoryEntry(
        session_id=state.session_id or f"sess-{int(time.time())}",
        saved_at=time.time(),
        project_name=project_name,
        started_at=state.started_at,
        last_turn=state.current_turn,
        duration_minutes=duration,
        active_modules=mods,
        files_touched=files,
        last_test_summary=last_test,
        excerpt=excerpt[:400],
        topics=topics,
    )
