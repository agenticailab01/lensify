"""Token-savings benchmark harness.

Models a realistic AI coding session and compares:
  - Baseline: agent reads files to answer questions (no lens)
  - With lens: agent reads the capsule, then targeted files only

Outputs a table similar to caveman's benchmark format so users can verify the
claim themselves.

Usage:
    python tests/benchmark.py path/to/project
    python tests/benchmark.py tests/fixtures/medium-project
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Make scripts importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "lensify"))

from scripts.scan import scan  # noqa: E402
from scripts.walker import walk  # noqa: E402
from scripts.capsule import estimate_tokens  # noqa: E402


# Average tokens per file an agent reads. Conservative middle estimate based on
# typical mixed source files (50-500 lines).
AVG_TOKENS_PER_FILE_READ = 350

# Typical session shape (configurable). These match the figures cited in our
# user-facing explainer.
ORIENTATION_READS_BASELINE = 30   # files an agent reads to "orient itself" without a lens
ORIENTATION_READS_WITH_LENS = 2   # files agent still reads, even with capsule
PER_Q_READS_BASELINE = 8          # files per follow-up question without lens
PER_Q_READS_WITH_LENS = 2         # files per follow-up question with lens
QUESTIONS_PER_SESSION = 8         # plausible coding session length


# Claude Opus pricing as of 2026-05 — adjust if needed
PRICE_INPUT_PER_MTOK = 15.0   # USD per million input tokens
PRICE_OUTPUT_PER_MTOK = 75.0  # USD per million output tokens


def run_benchmark(target: str) -> dict:
    """Estimate token + dollar savings for the given project."""
    target_path = Path(target).resolve()
    if not target_path.exists():
        print(json.dumps({"error": f"path not found: {target}"}), file=sys.stderr)
        sys.exit(2)

    # Measure actual project to size estimates correctly
    walk_result = walk(str(target_path))
    n_code_files = len(walk_result.code_files)

    # Build the lens (this is what the user would do once per repo)
    t0 = time.time()
    lens_data = scan(
        str(target_path),
        no_git=False,
        output_dir=str(target_path / "lensify-out"),
    )
    build_time = time.time() - t0
    capsule_tokens = lens_data.get("capsule_tokens", 0)

    # Compute orientation + per-question costs
    baseline_orient = ORIENTATION_READS_BASELINE * AVG_TOKENS_PER_FILE_READ
    with_lens_orient = capsule_tokens + (ORIENTATION_READS_WITH_LENS * AVG_TOKENS_PER_FILE_READ)

    baseline_per_q = PER_Q_READS_BASELINE * AVG_TOKENS_PER_FILE_READ
    with_lens_per_q = PER_Q_READS_WITH_LENS * AVG_TOKENS_PER_FILE_READ

    baseline_session = baseline_orient + QUESTIONS_PER_SESSION * baseline_per_q
    with_lens_session = with_lens_orient + QUESTIONS_PER_SESSION * with_lens_per_q

    saved_tok = baseline_session - with_lens_session
    saved_pct = saved_tok / baseline_session if baseline_session else 0.0
    saved_usd = saved_tok * PRICE_INPUT_PER_MTOK / 1_000_000

    rows = [
        ("Orientation",        baseline_orient,    with_lens_orient),
        (f"{QUESTIONS_PER_SESSION} follow-up questions",
            baseline_per_q * QUESTIONS_PER_SESSION,
            with_lens_per_q * QUESTIONS_PER_SESSION),
        ("Session total",      baseline_session,   with_lens_session),
    ]

    return {
        "project": str(target_path),
        "tier": lens_data["tier"],
        "files_scanned": n_code_files,
        "loc": lens_data["loc"],
        "capsule_tokens": capsule_tokens,
        "build_seconds": round(build_time, 2),
        "session_baseline_tokens": baseline_session,
        "session_with_lens_tokens": with_lens_session,
        "session_saved_tokens": saved_tok,
        "session_saved_pct": round(saved_pct * 100, 1),
        "session_saved_usd": round(saved_usd, 4),
        "rows": rows,
        "assumptions": {
            "avg_tokens_per_file_read": AVG_TOKENS_PER_FILE_READ,
            "orientation_reads_baseline": ORIENTATION_READS_BASELINE,
            "orientation_reads_with_lens": ORIENTATION_READS_WITH_LENS,
            "per_q_reads_baseline": PER_Q_READS_BASELINE,
            "per_q_reads_with_lens": PER_Q_READS_WITH_LENS,
            "questions_per_session": QUESTIONS_PER_SESSION,
            "price_input_usd_per_mtok": PRICE_INPUT_PER_MTOK,
        },
    }


def print_report(b: dict) -> None:
    print("=" * 72)
    print(f"Lensify benchmark for: {b['project']}")
    print(f"Tier: {b['tier']}  |  Files: {b['files_scanned']}  |  LOC: {b['loc']:,}")
    print(f"Lens build time: {b['build_seconds']}s   Capsule size: {b['capsule_tokens']} tok")
    print("=" * 72)
    print(f"{'Phase':<35} {'Without lens':>15} {'With lens':>15}")
    print("-" * 72)
    for name, base, with_lens in b["rows"]:
        print(f"{name:<35} {base:>12,} tok {with_lens:>12,} tok")
    print("-" * 72)
    print(f"Saved per session: {b['session_saved_tokens']:,} tok "
          f"({b['session_saved_pct']}%, ≈ ${b['session_saved_usd']})")
    print()
    print("Scaling estimates (assuming the same session shape repeats):")
    for n_sessions, label in [(20, "1 dev, ~1 month"), (200, "10-dev team, ~1 month"),
                              (2400, "10-dev team, ~1 year")]:
        usd = b["session_saved_usd"] * n_sessions
        print(f"  {label:<25} ≈ ${usd:,.2f} saved")
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lensify token-savings benchmark.")
    parser.add_argument("target", help="Path to project to benchmark")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args(argv)
    b = run_benchmark(args.target)
    if args.json:
        print(json.dumps(b, indent=2))
    else:
        print_report(b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
