"""Shared helpers for all framework adapter packs.

Two utilities every adapter needs:

    iter_python_with(parsed_files, walk_result, marker)
        Yield (rel_path, source_text) for Python files whose imports include
        the marker substring. The per-file import filter is the perf trick:
        skip every file that doesn't even mention the framework, so we never
        read it from disk. Typical AI codebase has ~5-20% of files importing
        any given framework → 80%+ I/O reduction.

    truncate(text, budget_tokens)
        Token-budget enforcement, delegating to capsule.truncate_to_tokens.

    line_of(text, char_offset)
        1-based line number from a regex match's start offset.

Underscore-prefixed so the registry's user-adapter loader skips it; the
manifest never references this file directly.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


# Per-file read cap (bytes). A 1 MB Python file is already exceptional;
# anything larger is almost certainly generated / vendored / a payload.
# Files over the cap are skipped silently — the adapter contributes no
# entries for them rather than blocking the scan.
#
# Override via the PROJECTLENS_MAX_READ_BYTES env var if you really need
# to surface huge files (rare).
def _max_read_bytes() -> int:
    raw = os.environ.get("PROJECTLENS_MAX_READ_BYTES", "")
    if raw.isdigit():
        return max(64 * 1024, int(raw))  # never less than 64 KB
    return 1 * 1024 * 1024  # 1 MB default


def _abs_path_for(walk_result, rel_path: str) -> str | None:
    for rec in walk_result.files:
        if rec.path == rel_path:
            return rec.abs_path
    return None


def safe_read(abs_path: str | Path) -> str | None:
    """Read a text file with a size cap. Returns None on miss / too large.

    All framework adapters that open files should funnel through this.
    Files larger than `_max_read_bytes()` are skipped — the adapter then
    contributes nothing for that file rather than blocking the scan.
    """
    p = Path(abs_path)
    try:
        size = p.stat().st_size
    except OSError:
        return None
    if size > _max_read_bytes():
        return None
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def iter_python_with(
    parsed_files, walk_result, marker: str,
) -> Iterator[tuple[str, str]]:
    """Yield (rel_path, source_text) for Python files importing `marker`."""
    marker_lower = marker.lower()
    for pf in parsed_files:
        if (pf.language or "").lower() != "python":
            continue
        imports = getattr(pf, "imports", None) or []
        if not any(marker_lower in (imp or "").lower() for imp in imports):
            continue
        abs_path = _abs_path_for(walk_result, pf.path)
        if not abs_path:
            continue
        text = safe_read(abs_path)
        if text is None:
            continue
        yield pf.path, text


def truncate(text: str, budget_tokens: int) -> str:
    """Defer to capsule.truncate_to_tokens; passthrough on import failure."""
    from importlib import import_module
    for name in ("scripts.capsule", "capsule"):
        try:
            mod = import_module(name)
            return mod.truncate_to_tokens(text, budget_tokens)
        except ImportError:
            continue
    return text


def line_of(text: str, char_offset: int) -> int:
    """1-based line number for a character offset (used after regex matches)."""
    return text[:char_offset].count("\n") + 1
