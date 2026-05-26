"""Statusline command for Claude Code (Phase 8).

This is invoked periodically by Claude Code's status bar. It must:
    - Read fast (< 50ms)
    - Print a single short line to stdout
    - Never crash (any failure → silent empty output)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from stats import load_stats, statusline_short, is_disabled
except ImportError:  # pragma: no cover
    sys.exit(0)


def main(argv: list[str] | None = None) -> int:
    if is_disabled():
        return 0
    try:
        stats = load_stats()
        # Skip the badge entirely on a fresh install (no events yet)
        if stats.tokens_saved == 0 and stats.dedup_count == 0 and stats.compressions == 0:
            return 0
        sys.stdout.write(statusline_short(stats) + "\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001 — statusline must never crash
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
