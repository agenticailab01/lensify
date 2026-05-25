"""CLI for /projectlens stats command (Phase 8).

Usage:
    python stats_cli.py            # print full lifetime report
    python stats_cli.py --json     # emit machine-readable JSON
    python stats_cli.py --short    # one-line summary (same as statusline)
    python stats_cli.py --reset    # wipe lifetime stats (asks confirmation)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from stats import (
        load_stats, save_stats, reset_stats, stats_report,
        statusline_short, usd_saved, format_number, format_bytes, stats_path,
    )
except ImportError:  # pragma: no cover
    print("projectlens stats unavailable (import failed)", file=sys.stderr)
    sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ProjectLens lifetime stats")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p.add_argument("--short", action="store_true", help="One-line summary only")
    p.add_argument("--reset", action="store_true", help="Wipe lifetime stats (asks confirmation)")
    p.add_argument("--yes", action="store_true", help="Skip confirmation for --reset")
    p.add_argument("--path", action="store_true", help="Print the stats file path and exit")
    args = p.parse_args(argv)

    if args.path:
        print(stats_path())
        return 0

    if args.reset:
        if not args.yes:
            answer = input(f"Reset lifetime stats at {stats_path()}? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted.")
                return 0
        reset_stats()
        print(f"Wiped {stats_path()}.")
        return 0

    stats = load_stats()

    if args.json:
        out = stats.to_dict()
        out["usd_saved_est"] = round(usd_saved(stats.tokens_saved), 4)
        out["statusline_short"] = statusline_short(stats)
        print(json.dumps(out, indent=2))
        return 0

    if args.short:
        print(statusline_short(stats))
        return 0

    print(stats_report(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
