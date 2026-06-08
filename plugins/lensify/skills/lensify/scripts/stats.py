"""Lifetime telemetry store (Phase 8).

Persists user-level cumulative savings across all sessions and all projects.
Each hook calls `record_event()` after its work; this module accumulates
totals and exposes formatting helpers for the statusline + `/lensify stats`.

Why this matters:
    The savings from the dedup hook, compression hook, capsule, and compactor
    are individually small per event but compounding. Without visible
    telemetry, users don't perceive the value. Making lifetime savings a
    statusline badge converts an invisible win into a sticky one — the same
    move that took Caveman from "interesting" to 62k stars.

Storage: ~/.lensify/stats.json
    User-level so it survives project deletion and is visible across all
    repos. Falls back to LENSIFY_STATS_HOME env var or cwd in tests.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

STATS_VERSION = 1
DEFAULT_HOME_DIRNAME = ".lensify"
STATS_FILENAME = "stats.json"

# Token estimate constants (used to convert non-token signals into token equivalents)
TOKENS_PER_DEDUPED_READ = 350      # average file Read replaced by a dedup advisory
TOKENS_PER_INJECT_SAVED = 850      # avg full-capsule vs. selective injection delta
BYTES_PER_TOKEN = 3.5              # conservative bytes→tokens ratio (matches capsule.py)

# Per-model input pricing (USD per million tokens). Override via LENSIFY_USD_PER_MTOK.
MODEL_PRICING: dict[str, float] = {
    "opus":    15.0,   # claude-opus-4-x
    "sonnet":   3.0,   # claude-sonnet-4-x
    "haiku":    0.80,  # claude-haiku-4-x
}
DEFAULT_USD_PER_MTOK = 15.0  # fallback when model is unknown


def _detect_usd_per_mtok() -> float:
    """Auto-detect pricing from env var, persisted model file, or fall back to Opus rate."""
    env_override = os.environ.get("LENSIFY_USD_PER_MTOK")
    if env_override:
        try:
            return float(env_override)
        except ValueError:
            pass
    # Try env var first, then the model file written by SessionStart hook
    model = (os.environ.get("CLAUDE_MODEL") or "").lower()
    if not model:
        try:
            model_file = Path.home() / ".lensify" / "current_model"
            model = model_file.read_text(encoding="utf-8").strip().lower()
        except OSError:
            pass
    for key, price in MODEL_PRICING.items():
        if key in model:
            return price
    return DEFAULT_USD_PER_MTOK


# ---- File location ----

def stats_home() -> Path:
    """Resolve the directory for stats.json.

    Order:
        1. $LENSIFY_STATS_HOME (used by tests + power users)
        2. ~/.lensify
    """
    env = os.environ.get("LENSIFY_STATS_HOME")
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
    #   tokens_saved      = grand total (realized + potential) — kept for continuity
    #   tokens_realized   = savings that actually left the context window
    #                       (dedup denies that blocked a re-read, compactor reclaim)
    #   tokens_potential  = savings that would land only if a mechanism is enforced
    #                       or a later compaction drops the raw blob (advisory dedup,
    #                       tool-output compression, selective injection)
    tokens_saved: int = 0
    tokens_realized: int = 0
    tokens_potential: int = 0

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
        # Realized/potential split (added v0.16). Legacy files have only
        # `tokens_saved` — treat that whole legacy total as *potential*, since
        # the pre-split mechanisms (advisory dedup, compression) never actually
        # evicted tokens. Honest by construction.
        realized = int(data.get("tokens_realized", 0))
        saved = int(data.get("tokens_saved", 0))
        potential = int(data.get("tokens_potential", max(0, saved - realized)))
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
            tokens_saved=saved,
            tokens_realized=realized,
            tokens_potential=potential,
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
    "dedup",            # a duplicate Read was flagged (advisory → potential)
    "dedup_denied",     # a duplicate Read was *blocked* (deny → realized saving)
    "compression",      # a tool output was compressed (provides bytes_saved)
    "compactor",        # /lensify compact ran (provides tokens_reclaimed)
    "memory_recall",    # SessionStart loaded ≥1 past memory
    "memory_save",      # a session memory was persisted
    "selective_inject", # UserPromptSubmit picked a subset of sections
    "scan",             # /lensify scan ran
}


def record_event(
    event: str,
    *,
    project_root: str | None = None,
    bytes_saved: int = 0,
    tokens_saved: int = 0,
    realized: bool = False,
    extra: dict | None = None,
) -> None:
    """Idempotent counter update for a single hook event.

    Safe to call from any hook. Never raises — telemetry failure must never
    cascade into agent failure. Respects LENSIFY_STATS=0 opt-out.

    `realized=True` forces an event that is normally counted as *potential*
    (e.g. compression) into the *realized* bucket. The `lensify run` wrapper
    uses this: it compresses before the output ever reaches the model, so the
    saving genuinely lands.
    """
    if is_disabled():
        return
    if event not in EVENT_TYPES:
        return
    try:
        stats = load_stats()
        _apply_event(stats, event, bytes_saved=bytes_saved, tokens_saved=tokens_saved,
                     project_root=project_root, extra=extra, force_realized=realized)
        save_stats(stats)
    except Exception:  # noqa: BLE001
        pass


def _apply_event(stats: LifetimeStats, event: str, *,
                 bytes_saved: int, tokens_saved: int,
                 project_root: str | None, extra: dict | None,
                 force_realized: bool = False) -> None:
    """Pure in-memory update. Separated for testability."""
    def _credit(tok: int, *, realized: bool) -> None:
        realized = realized or force_realized
        """Add tokens to the grand total and the realized/potential bucket."""
        stats.tokens_saved += tok
        if realized:
            stats.tokens_realized += tok
        else:
            stats.tokens_potential += tok

    # Compute per-event token delta when the caller didn't supply one
    if event == "dedup":
        # Advisory only — the re-read still happened. Counts as potential.
        stats.dedup_count += 1
        if tokens_saved == 0:
            tokens_saved = TOKENS_PER_DEDUPED_READ
        _credit(tokens_saved, realized=False)
    elif event == "dedup_denied":
        # The duplicate Read was blocked — those tokens never re-entered context.
        stats.dedup_count += 1
        if tokens_saved == 0:
            tokens_saved = TOKENS_PER_DEDUPED_READ
        _credit(tokens_saved, realized=True)
    elif event == "compression":
        # Raw output is not evicted from the current turn — only a later
        # compaction may drop it. Counts as potential until that happens.
        stats.compressions += 1
        stats.compress_bytes_saved += max(0, bytes_saved)
        if tokens_saved == 0 and bytes_saved > 0:
            tokens_saved = int(bytes_saved / BYTES_PER_TOKEN)
        _credit(tokens_saved, realized=False)
    elif event == "compactor":
        # Compaction physically rewrites the transcript — realized.
        stats.compactor_runs += 1
        _credit(tokens_saved, realized=True)
    elif event == "memory_recall":
        stats.memory_recalls += 1
        # Memory recall savings are not directly measurable; count only.
    elif event == "memory_save":
        stats.memory_saves += 1
    elif event == "selective_inject":
        # Saving vs. injecting the whole capsule — only counts if the full
        # capsule would otherwise have been injected. Potential.
        stats.selective_injections += 1
        if tokens_saved == 0:
            tokens_saved = TOKENS_PER_INJECT_SAVED
        _credit(tokens_saved, realized=False)
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
        if event in ("dedup", "dedup_denied"):
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
    """Opt out via LENSIFY_STATS=0."""
    val = os.environ.get("LENSIFY_STATS")
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
    """Convert token savings into a rough USD estimate using auto-detected model pricing."""
    rate = usd_per_mtok if usd_per_mtok is not None else _detect_usd_per_mtok()
    return (tokens / 1_000_000.0) * rate


# ---- Statusline + CLI formatters ----

def statusline_short(stats: LifetimeStats) -> str:
    """The short form for Claude Code's statusline badge.

    Headlines *realized* savings (tokens that actually left the window) so the
    badge never overstates. Potential savings are shown as a muted suffix to
    nudge users toward enforce mode.

    Aim for ~30 chars. Examples:
        [LENS] ⛏ 12.4k · 8d · 2c
        [LENS] ⛏ 0 (+9.1k pot) · 26d
    """
    parts = [f"⛏ {format_number(stats.tokens_realized)}"]
    if stats.tokens_potential:
        parts[0] += f" (+{format_number(stats.tokens_potential)} pot)"
    if stats.dedup_count or stats.compactor_runs:
        deets = []
        if stats.dedup_count:
            deets.append(f"{format_number(stats.dedup_count)}d")
        if stats.compactor_runs:
            deets.append(f"{stats.compactor_runs}c")
        parts.append(" · ".join(deets))
    return "[LENS] " + " · ".join(parts)


def stats_report(stats: LifetimeStats) -> str:
    """Detailed multi-line report for `/lensify stats`.

    Includes lifetime totals, per-phase breakdown, top projects.
    """
    rate = _detect_usd_per_mtok()
    usd = usd_saved(stats.tokens_realized, usd_per_mtok=rate)
    age_days = max(0.0, (time.time() - stats.created_at) / 86_400.0)

    model = (os.environ.get("CLAUDE_MODEL") or "").lower()
    if "sonnet" in model:
        model_label = "Sonnet"
    elif "haiku" in model:
        model_label = "Haiku"
    else:
        model_label = "Opus"

    out = [
        "Lensify — lifetime stats",
        "=" * 40,
        f"Tracking since:   {time.strftime('%Y-%m-%d', time.localtime(stats.created_at))} "
        f"({int(age_days)} day(s) ago)",
        f"Tokens saved (realized):  {stats.tokens_realized:,}",
        f"Estimated $ saved:        ~${usd:.2f}  (realized only, at {model_label} "
        f"pricing ${rate:.2f}/M tok)",
        f"Potential (not realized): {stats.tokens_potential:,}  "
        f"— set LENSIFY_DEDUP_ENFORCE=1 to capture repeat-read savings",
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
    """Wipe lifetime stats. Used by `/lensify stats --reset`."""
    path = stats_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
