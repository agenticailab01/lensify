"""Within-session state for the Read Dedup Hook.

Tracks which files the agent has already read in the current Claude session,
keyed by absolute path + content hash. Persists to .lensify-session.json
in the project root.

Design constraints:
    - Pure stdlib (must run inside a Claude Code hook with no pip install).
    - Robust to malformed or missing state files (never crash the agent).
    - Atomic writes (no partial state on power loss / race).
    - Bounded size — caps at MAX_TRACKED_READS to prevent unbounded growth.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

STATE_FILENAME = ".lensify-session.json"
MAX_TRACKED_READS = 500    # hard cap — prevents a runaway from filling the file
HASH_BYTES = 16            # short SHA-256 prefix; cheap, low collision risk
STATE_VERSION = 1


@dataclass
class ReadRecord:
    """One tracked file read."""
    rel_path: str               # relative to project root, POSIX style
    abs_path: str               # absolute path on disk
    content_hash: str           # short SHA-256 of file contents at read time
    first_turn: int             # turn number when first read
    last_turn: int              # turn number when last read
    read_count: int = 1         # how many times the agent has tried to read this file
    size_bytes: int = 0
    first_seen_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EditRecord:
    """An Edit/Write tool invocation."""
    rel_path: str
    abs_path: str
    turn: int
    op: str = "edit"             # "edit" | "write"
    at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BashRecord:
    """A Bash invocation."""
    command: str                  # truncated to ~120 chars for log compactness
    turn: int
    exit_status: int | None = None  # if PostToolUse captured it
    at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TestResult:
    """Latest detected pytest/jest/etc. outcome — best-effort regex parse."""
    framework: str               # "pytest" | "jest" | "go" | "unknown"
    passed: int = 0
    failed: int = 0
    failing_tests: list[str] = field(default_factory=list)
    captured_at: float = field(default_factory=time.time)
    turn: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SessionState:
    """Aggregate session state for a single project."""
    version: int = STATE_VERSION
    session_id: str = ""
    project_root: str = ""
    started_at: float = field(default_factory=time.time)
    current_turn: int = 0
    reads: dict[str, ReadRecord] = field(default_factory=dict)  # key = abs_path
    edits: list[EditRecord] = field(default_factory=list)
    bash_history: list[BashRecord] = field(default_factory=list)
    last_test: TestResult | None = None
    compressions: list[dict] = field(default_factory=list)  # Phase 6 telemetry

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "session_id": self.session_id,
            "project_root": self.project_root,
            "started_at": self.started_at,
            "current_turn": self.current_turn,
            "reads": {k: v.to_dict() for k, v in self.reads.items()},
            "edits": [e.to_dict() for e in self.edits],
            "bash_history": [b.to_dict() for b in self.bash_history],
            "last_test": self.last_test.to_dict() if self.last_test else None,
            "compressions": list(self.compressions),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        reads_raw = data.get("reads", {}) or {}
        reads = {}
        for k, v in reads_raw.items():
            if not isinstance(v, dict):
                continue
            # Tolerate missing fields from older versions
            reads[k] = ReadRecord(
                rel_path=v.get("rel_path", ""),
                abs_path=v.get("abs_path", k),
                content_hash=v.get("content_hash", ""),
                first_turn=int(v.get("first_turn", 0)),
                last_turn=int(v.get("last_turn", 0)),
                read_count=int(v.get("read_count", 1)),
                size_bytes=int(v.get("size_bytes", 0)),
                first_seen_at=float(v.get("first_seen_at", time.time())),
            )
        edits = []
        for e in data.get("edits", []) or []:
            if isinstance(e, dict):
                edits.append(EditRecord(
                    rel_path=e.get("rel_path", ""),
                    abs_path=e.get("abs_path", ""),
                    turn=int(e.get("turn", 0)),
                    op=e.get("op", "edit"),
                    at=float(e.get("at", time.time())),
                ))
        bash = []
        for b in data.get("bash_history", []) or []:
            if isinstance(b, dict):
                bash.append(BashRecord(
                    command=b.get("command", ""),
                    turn=int(b.get("turn", 0)),
                    exit_status=b.get("exit_status"),
                    at=float(b.get("at", time.time())),
                ))
        last_test = None
        lt = data.get("last_test")
        if isinstance(lt, dict):
            last_test = TestResult(
                framework=lt.get("framework", "unknown"),
                passed=int(lt.get("passed", 0)),
                failed=int(lt.get("failed", 0)),
                failing_tests=list(lt.get("failing_tests", []) or []),
                captured_at=float(lt.get("captured_at", time.time())),
                turn=int(lt.get("turn", 0)),
            )
        compressions = list(data.get("compressions", []) or [])
        return cls(
            version=int(data.get("version", STATE_VERSION)),
            session_id=str(data.get("session_id", "")),
            project_root=str(data.get("project_root", "")),
            started_at=float(data.get("started_at", time.time())),
            current_turn=int(data.get("current_turn", 0)),
            reads=reads,
            edits=edits,
            bash_history=bash,
            last_test=last_test,
            compressions=compressions,
        )


def _state_path(project_root: str | Path) -> Path:
    return Path(project_root) / STATE_FILENAME


def load_state(project_root: str | Path) -> SessionState:
    """Read state from disk. Returns a fresh state if the file is missing or invalid."""
    path = _state_path(project_root)
    if not path.exists():
        return SessionState(project_root=str(Path(project_root).resolve()))
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("state file is not a JSON object")
        return SessionState.from_dict(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        # Corrupted state file — start fresh, but don't crash the hook.
        _log_warn(f"corrupted session state at {path}: {exc}; resetting")
        return SessionState(project_root=str(Path(project_root).resolve()))


def save_state(state: SessionState, project_root: str | Path) -> None:
    """Atomic write of state to disk. Never raises."""
    path = _state_path(project_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file in the same directory, then rename — atomic on POSIX.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False,
            dir=str(path.parent), prefix=".lensify-session-", suffix=".tmp",
        ) as tmp:
            json.dump(state.to_dict(), tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, path)
    except OSError as exc:
        _log_warn(f"failed to write session state: {exc}")


def reset_state(project_root: str | Path, session_id: str = "") -> SessionState:
    """Start a fresh session. Called by the SessionStart hook."""
    state = SessionState(
        session_id=session_id,
        project_root=str(Path(project_root).resolve()),
        started_at=time.time(),
        current_turn=0,
    )
    save_state(state, project_root)
    return state


def compute_hash(file_path: str | Path) -> str | None:
    """Return short SHA-256 of file contents, or None if file unreadable."""
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[: HASH_BYTES * 2]
    except (OSError, IOError):
        return None


def to_relative(abs_path: str | Path, project_root: str | Path) -> str:
    """Best-effort relative path; falls back to absolute if outside project."""
    try:
        rel = Path(abs_path).resolve().relative_to(Path(project_root).resolve())
        return str(rel).replace(os.sep, "/")
    except ValueError:
        return str(abs_path)


@dataclass
class DedupDecision:
    """The result of checking whether a read is a duplicate."""
    is_duplicate: bool
    is_modified: bool                  # True if file was read before but content changed
    previous_record: ReadRecord | None
    note: str                          # human-readable message for the agent
    new_record: ReadRecord             # the record now stored in state


def check_and_record(
    state: SessionState,
    file_path: str | Path,
    project_root: str | Path,
) -> DedupDecision:
    """Check whether file has been read before in this session, then record it.

    Always updates state. Returns a decision describing what the hook should
    surface to the agent.
    """
    abs_path = str(Path(file_path).resolve())
    rel_path = to_relative(abs_path, project_root)
    content_hash = compute_hash(abs_path) or ""
    try:
        size = os.path.getsize(abs_path)
    except OSError:
        size = 0

    prev = state.reads.get(abs_path)
    if prev is None:
        # First time we've seen this file
        new_rec = ReadRecord(
            rel_path=rel_path,
            abs_path=abs_path,
            content_hash=content_hash,
            first_turn=state.current_turn,
            last_turn=state.current_turn,
            read_count=1,
            size_bytes=size,
        )
        state.reads[abs_path] = new_rec
        _enforce_cap(state)
        return DedupDecision(
            is_duplicate=False, is_modified=False, previous_record=None,
            note="", new_record=new_rec,
        )

    # We've read this file before in this session.
    is_modified = bool(content_hash) and content_hash != prev.content_hash
    prev_turn = prev.first_turn
    new_rec = ReadRecord(
        rel_path=rel_path,
        abs_path=abs_path,
        content_hash=content_hash or prev.content_hash,
        first_turn=prev.first_turn,
        last_turn=state.current_turn,
        read_count=prev.read_count + 1,
        size_bytes=size or prev.size_bytes,
        first_seen_at=prev.first_seen_at,
    )
    state.reads[abs_path] = new_rec

    if is_modified:
        note = (
            f"DEDUP: `{rel_path}` was already read earlier in this session "
            f"(turn {prev_turn}) but its contents have changed since. "
            f"Re-reading is appropriate."
        )
    else:
        note = (
            f"DEDUP: `{rel_path}` was already read in this session at turn "
            f"{prev_turn}. The file's contents have NOT changed (sha256 "
            f"unchanged). If you already have the information you need from "
            f"the earlier read, consider skipping this read and proceeding."
        )

    return DedupDecision(
        is_duplicate=True, is_modified=is_modified, previous_record=prev,
        note=note, new_record=new_rec,
    )


def increment_turn(state: SessionState) -> None:
    """Bump the turn counter. Called once per user prompt."""
    state.current_turn += 1


# ----- Activity recording (Phase 2) -----

MAX_EDITS = 200
MAX_BASH = 100


def record_edit(state: SessionState, file_path: str | Path, project_root: str | Path,
                op: str = "edit") -> EditRecord:
    """Record an Edit or Write tool invocation."""
    abs_path = str(Path(file_path).resolve())
    rel_path = to_relative(abs_path, project_root)
    rec = EditRecord(
        rel_path=rel_path, abs_path=abs_path, turn=state.current_turn, op=op,
    )
    state.edits.append(rec)
    if len(state.edits) > MAX_EDITS:
        state.edits = state.edits[-MAX_EDITS:]
    return rec


def record_bash(state: SessionState, command: str, exit_status: int | None = None) -> BashRecord:
    """Record a Bash invocation. Command truncated to ~120 chars."""
    truncated = command if len(command) <= 120 else command[:117] + "..."
    rec = BashRecord(
        command=truncated, turn=state.current_turn, exit_status=exit_status,
    )
    state.bash_history.append(rec)
    if len(state.bash_history) > MAX_BASH:
        state.bash_history = state.bash_history[-MAX_BASH:]
    return rec


# Regex patterns for cheap test-result detection. Order matters: most specific first.
_TEST_PATTERNS = [
    # pytest: "==== 23 passed, 2 failed in 1.02s ===="
    ("pytest", re.compile(r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?", re.IGNORECASE)),
    # pytest alt: "==== 2 failed, 23 passed in 1.02s ===="
    ("pytest", re.compile(r"(\d+)\s+failed,\s*(\d+)\s+passed", re.IGNORECASE)),
    # jest: "Tests: 23 passed, 2 failed, 25 total"
    ("jest", re.compile(r"Tests:\s+(?:(\d+)\s+failed,\s*)?(\d+)\s+passed", re.IGNORECASE)),
    # go test: "PASS" / "FAIL" / "ok ... 0.123s"
    ("go", re.compile(r"^(PASS|FAIL)\b", re.MULTILINE)),
]
_PYTEST_FAILING_RE = re.compile(r"^FAILED\s+(\S+::\S+)", re.MULTILINE)


def parse_test_output(output: str) -> TestResult | None:
    """Best-effort parser for common test framework outputs.

    Returns None if no recognizable signal is present. Order matters — the
    most specific patterns are tried first so we don't mis-classify a jest
    output as pytest (etc.).
    """
    if not output:
        return None
    out = output[-8000:]  # cap input length to keep regex cheap

    # Jest first — it has a distinctive "Tests:" header
    if re.search(r"Tests:\s+", out, re.IGNORECASE):
        m = re.search(r"Tests:\s+(?:(\d+)\s+failed,\s*)?(\d+)\s+passed", out, re.IGNORECASE)
        if m:
            failed = int(m.group(1)) if m.group(1) else 0
            passed = int(m.group(2))
            return TestResult(framework="jest", passed=passed, failed=failed)

    # pytest "M failed, N passed" (more specific — try BEFORE the bare "N passed" pattern)
    m = re.search(r"(\d+)\s+failed,\s*(\d+)\s+passed", out, re.IGNORECASE)
    if m:
        failed = int(m.group(1))
        passed = int(m.group(2))
        failing = [m2.group(1) for m2 in _PYTEST_FAILING_RE.finditer(out)][:10]
        return TestResult(framework="pytest", passed=passed, failed=failed, failing_tests=failing)

    # pytest "N passed[, M failed]"
    m = re.search(r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?", out, re.IGNORECASE)
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2)) if m.group(2) else 0
        failing = [m2.group(1) for m2 in _PYTEST_FAILING_RE.finditer(out)][:10]
        return TestResult(framework="pytest", passed=passed, failed=failed, failing_tests=failing)

    # go test
    if re.search(r"^FAIL\b", out, re.MULTILINE):
        return TestResult(framework="go", failed=1)
    if re.search(r"^ok\s+\S+\s+[\d.]+s", out, re.MULTILINE):
        return TestResult(framework="go", passed=1)

    return None


def record_test_result(state: SessionState, result: TestResult) -> None:
    """Store the latest test outcome (overwrites previous)."""
    result.turn = state.current_turn
    state.last_test = result


# Top-N modules the agent has been active in, based on recent edits + reads
def active_modules(state: SessionState, top_n: int = 5) -> list[tuple[str, int]]:
    """Return [(top-level-module, activity-score), …] sorted by recency × frequency."""
    score: dict[str, float] = {}
    now = time.time()
    # Edits weighted higher than reads
    for e in state.edits:
        top = e.rel_path.split("/")[0] if "/" in e.rel_path else e.rel_path
        if not top:
            continue
        age = max(1.0, now - e.at)
        score[top] = score.get(top, 0.0) + (3.0 / age) * 1.0
    for r in state.reads.values():
        top = r.rel_path.split("/")[0] if "/" in r.rel_path else r.rel_path
        if not top:
            continue
        age = max(1.0, now - r.first_seen_at)
        score[top] = score.get(top, 0.0) + (1.0 / age) * float(r.read_count)
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    return [(k, int(v * 100)) for k, v in ranked[:top_n]]


def _enforce_cap(state: SessionState) -> None:
    """Drop the oldest records if we exceed the cap. Keeps the file bounded."""
    if len(state.reads) <= MAX_TRACKED_READS:
        return
    # Drop oldest by first_seen_at
    sorted_items = sorted(state.reads.items(), key=lambda kv: kv[1].first_seen_at)
    overflow = len(sorted_items) - MAX_TRACKED_READS
    for key, _ in sorted_items[:overflow]:
        state.reads.pop(key, None)


def session_summary(state: SessionState) -> dict[str, Any]:
    """Return a small dict describing the session state — for diagnostics."""
    total_reads = sum(r.read_count for r in state.reads.values())
    duplicates_avoided = total_reads - len(state.reads)
    return {
        "files_tracked": len(state.reads),
        "total_read_attempts": total_reads,
        "duplicates_alerted": duplicates_avoided,
        "session_id": state.session_id,
        "current_turn": state.current_turn,
    }


def _log_warn(msg: str) -> None:
    """Best-effort diagnostic logging to stderr. Never raises."""
    try:
        import sys
        print(f"[lensify-dedup] {msg}", file=sys.stderr)
    except Exception:
        pass


def is_disabled() -> bool:
    """Allow users to opt out via LENSIFY_DEDUP=0."""
    return os.environ.get("LENSIFY_DEDUP", "1") in ("0", "false", "no", "off")
