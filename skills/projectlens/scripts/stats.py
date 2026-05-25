"""Lifetime telemetry store (Phase 8).

Persists user-level cumulative savings across all sessions and all projects.
Each hook calls `record_event()` after its work; this module accumulates
totals and exposes formatting helpers for the statusline + `/projectlens stats`.

Why this matters:
    The savings from the dedup hook, compression hook, capsule, and compactor
    are individually small per event but compounding. Without visible
    telemetry, users don't perceive the value. Making lifetime savings a
    statusline badge converts an invisible win into a sticky one — the same
    move that took Caveman from "interesting" to 62k stars.

Storage: ~/.projectlens/stats.json
    User-level so it survives project deletion and is visible across all
    repos. Falls back to PROJECTLENS_STATS_HOME env var or cwd in tests.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

STATS_VERSION = 1
DEFAULT_HOME_DIRNAME = ".projectlens"
STATS_FILENAME = "stats.json"

# Token estimate constants (used to convert non-token signals into token equivalents)
TOKENS_PER_DEDUPED_READ = 350      # average file Read replaced by a dedup advisory
TOKENS_PER_INJECT_SAVED = 850      # avg full-capsule vs. selective injection delta
BYTES_PER_TOKEN = 3.5              # conservative bytes→tokens ratio (matches capsule.py)

# Default Claude Opus input pricing for the USD-saved estimate. Override via env.
DEFAULT_USD_PER_MTOK = 15.0


# ---- File location ----

def stats_home() -> Path:
    """Resolve the directory for stats.json.

    Order:
        1. $PROJECTLENS_STATS_HOME (used by tests + power users)
        2. ~/.projectlens
    """
    env = os.environ.get("PROJECTLENS_STATS_HOME")
    if env:
        return Path(env)
    return Path.home() / DEFAULT_HOME_DIRNAME


def stats_path() -> Path:
    return stats_home() / STATS_FILENAME


# ---- Data shape ----

@dataclass
class LifetimeStats:
    """All counters live here. Add fields freely — load_stats tolerates
    older files via dict.get()."""
    version: int = STATS_VERSION
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    # Cumulative event counts
    dedup_count: int = 0
    compactor_runs: int = 0
    memory_recalls: int = 0
    memory_saves: int = 0
    compressions: int = 0
    selective_injections: int = 0
    scan_count: int = 0

    # Cumulative token signals (always in tokens)
    tokens_saved: int = 0

    # Cumulative byte signal from compression (kept separately for the
    # "X MB of raw output compressed" stat)
    compress_bytes_saved: int = 0

    # Per-project totals — keyed by project root
    by_project: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LifetimeStats":
        if not isinstance(data, dict):
            return cls()
        return cls(
            version=int(data.get("version", STATS_VERSION)),
            created_at=float(data.get("created_at", time.time())),
            last_updated=float(data.get("last_updated", time.time())),
            dedup_count=int(data.get("dedup_count", 0)),
            compactor_runs=int(data.get("compactor_runs", 0)),
            memory_recalls=int(data.get("memory_recalls", 0)),
            memory_saves=int(data.get("memory_saves", 0)),
            compressions=int(data.get("compressions", 0)),
            selective_injections=int(data.get("selective_injections", 0)),
            scan_count=int(data.get("scan_count", 0)),
            tokens_saved=int(data.get("tokens_saved", 0)),
            compress_bytes_saved=int(data.get("compress_bytes_saved", 0)),
            by_project=dict(data.get("by_project", {}) or {}),
        )


# ---- I/O ----

def load_stats() -> LifetimeStats:
    """Read the lifetime stats file. Returns fresh stats if missing/corrupt."""
    path = stats_path()
    if not path.exists():
        return LifetimeStats()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return LifetimeStats.from_dict(data)
    except (OSError, json.JSONDecodeError, ValueError):
        return LifetimeStats()


def save_stats(stats: LifetimeStats) -> None:
    """Atomic write. Never raises."""
    stats.last_updated = time.time()
    path = stats_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False,
            dir=str(path.parent), prefix=".pl-stats-", suffix=".tmp",
        ) as tmp:
            json.dump(stats.to_dict(), tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, path)
    except OSError:
        # Best-effort; statusline failure shouldn't break agent operations
        pass


# ---- Event recording ----

EVENT_TYPES = {
    "dedup",            # a duplicate Read was flagged
    "compression",      # a tool output was compressed (provides bytes_saved)
    "compactor",        # /projectlens compact ran (provides tokens_reclaimed)
    "memory_recall",    # SessionStart loaded ≥1 past memory
    "memory_save",      # a session memory was persisted
    "selective_inject", # UserPromptSubmit picked a subset of sections
    "scan",             # /projectlens scan ran
}


def record_event(
    event: str,
    *,
    project_root: str | None = None,
    bytes_saved: int = 0,
    tokens_saved: int = 0,
    extra: dict | None = None,
) -> None:
    """Idempotent counter update for a single hook event.

    Safe to call from any hook. Never raises — telemetry failure must never
    cascade into agent failure. Respects PROJECTLENS_STATS=0 opt-out.
    """
    if is_disabled():
        return
    if event not in EVENT_TYPES:
        return
    try:
        stats = load_stats()
        _apply_event(stats, event, bytes_saved=bytes_saved, tokens_saved=tokens_saved,
                     project_root=project_root, extra=extra)
        save_stats(stats)
    except Exception:  # noqa: BLE001
        pass


def _apply_event(stats: LifetimeStats, event: str, *,
                 bytes_saved: int, tokens_saved: int,
                 project_root: str | None, extra: dict | None) -> None:
    """Pure in-memory update. Separated for testability."""
    # Compute per-event token delta when the caller didn't supply one
    if event == "dedup":
        stats.dedup_count += 1
        if tokens_saved == 0:
            tokens_saved = TOKENS_PER_DEDUPED_READ
        stats.tokens_saved += tokens_saved
    elif event == "compression":
        stats.compressions += 1
        stats.compress_bytes_saved += max(0, bytes_saved)
        if tokens_saved == 0 and bytes_saved > 0:
            tokens_saved = int(bytes_saved / BYTES_PER_TOKEN)
        stats.tokens_saved += tokens_saved
    elif event == "compactor":
        stats.compactor_runs += 1
        stats.tokens_saved += tokens_saved
    elif event == "memory_recall":
        stats.memory_recalls += 1
        # Memory recall savings are not directly measurable; count only.
    elif event == "memory_save":
        stats.memory_saves += 1
    elif event == "selective_inject":
        stats.selective_injections += 1
        if tokens_saved == 0:
            tokens_saved = TOKENS_PER_INJECT_SAVED
        stats.tokens_saved += tokens_saved
    elif event == "scan":
        stats.scan_count += 1

    # Per-project bucket
    if project_root:
        bucket = stats.by_project.setdefault(project_root, {
            "tokens_saved": 0,
            "dedup_count": 0,
            "compressions": 0,
            "compactor_runs": 0,
        })
        if event == "dedup":
            bucket["dedup_count"] = int(bucket.get("dedup_count", 0)) + 1
            bucket["tokens_saved"] = int(bucket.get("tokens_saved", 0)) + tokens_saved
        elif event == "compression":
            bucket["compressions"] = int(bucket.get("compressions", 0)) + 1
            bucket["tokens_saved"] = int(bucket.get("tokens_saved", 0)) + tokens_saved
        elif event == "compactor":
            bucket["compactor_runs"] = int(bucket.get("compactor_runs", 0)) + 1
            bucket["tokens_saved"] = int(bucket.get("tokens_saved", 0)) + tokens_saved
        elif event == "selective_inject":
            bucket["tokens_saved"] = int(bucket.get("tokens_saved", 0)) + tokens_saved


def is_disabled() -> bool:
    """Opt out via PROJECTLENS_STATS=0."""
    val = os.environ.get("PROJECTLENS_STATS")
    return val in ("0", "false", "no", "off")


# ---- Formatting helpers ----

def format_number(n: int) -> str:
    """Compact number format. 1234 -> '1.2k', 1234567 -> '1.2M'."""
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return f"{n/1_000_000:.1f}M".replace(".0M", "M")


def format_bytes(n: int) -> str:
    """Compact bytes format."""
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f}KB".replace(".0KB", "KB")
    return f"{n/(1024*1024):.1f}MB".replace(".0MB", "MB")


def usd_saved(tokens: int, usd_per_mtok: float | None = None) -> float:
    """Convert token savings into a rough USD estimate at Opus input pricing."""
    rate = usd_per_mtok
    if rate is None:
        env = os.environ.get("PROJECTLENS_USD_PER_MTOK")
        try:
            rate = float(env) if env else DEFAULT_USD_PER_MTOK
        except ValueError:
            rate = DEFAULT_USD_PER_MTOK
    return (tokens / 1_000_000.0) * rate


# ---- Statusline + CLI formatters ----

def statusline_short(stats: LifetimeStats) -> str:
    """The short form for Claude Code's statusline badge.

    Aim for ~30 chars. Examples:
        [LENS] ⛏ 47.2k tok
        [LENS] ⛏ 12.4k · 8d · 2c
    """
    parts = [f"⛏ {format_number(stats.tokens_saved)}"]
    if stats.dedup_count or stats.compactor_runs:
        deets = []
        if stats.dedup_count:
            deets.append(f"{format_number(stats.dedup_count)}d")
        if stats.compactor_runs:
            deets.append(f"{stats.compactor_runs}c")
        parts.append(" · ".join(deets))
    return "[LENS] " + " · ".join(parts)


def stats_report(stats: LifetimeStats) -> str:
    """Detailed multi-line report for `/projectlens stats`.

    Includes lifetime totals, per-phase breakdown, top projects.
    """
    usd = usd_saved(stats.tokens_saved)
    age_days = max(0.0, (time.time() - stats.created_at) / 86_400.0)

    out = [
        "ProjectLens — lifetime stats",
        "=" * 40,
        f"Tracking since:   {time.strftime('%Y-%m-%d', time.localtime(stats.created_at))} "
        f"({int(age_days)} day(s) ago)",
        f"Tokens saved:     {stats.tokens_saved:,}",
        f"Estimated $ saved: ~${usd:.2f}  (at Opus input pricing)",
        "",
        "By event type:",
        f"  Dedup hooks       {stats.dedup_count:6d} events  "
        f"(~{stats.dedup_count * TOKENS_PER_DEDUPED_READ:,} tok)",
        f"  Compressions      {stats.compressions:6d} events  "
        f"(~{int(stats.compress_bytes_saved / BYTES_PER_TOKEN):,} tok, "
        f"{format_bytes(stats.compress_bytes_saved)} raw)",
        f"  Compactor runs    {stats.compactor_runs:6d} runs",
        f"  Memory recalls    {stats.memory_recalls:6d} events",
        f"  Memory saves      {stats.memory_saves:6d} events",
        f"  Selective inject  {stats.selective_injections:6d} prompts",
        f"  Scans             {stats.scan_count:6d} runs",
    ]

    if stats.by_project:
        out.append("")
        out.append("Top projects by tokens saved:")
        ranked = sorted(
            stats.by_project.items(),
            key=lambda kv: int(kv[1].get("tokens_saved", 0)),
            reverse=True,
        )
        for path, bucket in ranked[:5]:
            disp_path = path
            if len(disp_path) > 50:
                disp_path = "…" + disp_path[-49:]
            out.append(
                f"  {disp_path:<50}  {int(bucket.get('tokens_saved', 0)):>10,} tok"
            )

    return "\n".join(out)


# ---- Reset (for testing + user invocation) ----

def reset_stats() -> None:
    """Wipe lifetime stats. Used by `/projectlens stats --reset`."""
    path = stats_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
