"""Tests for the `lensify run` wrapper — realized output compression.

The wrapper executes a command and prints a *compressed* summary instead of the
raw output, so the bytes never reach the model's context window. The command's
exit code is preserved.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCAN = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "lensify" / "skills" / "lensify" / "scripts" / "scan.py"
)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCAN), "run", *args],
        capture_output=True, text=True, cwd=str(cwd), timeout=20,
    )


def test_large_output_is_compressed(tmp_path):
    # Emit ~6KB so it crosses MIN_COMPRESS_BYTES.
    payload = "print('x' * 6000)"
    proc = run(["--", sys.executable, "-c", payload], tmp_path)
    assert proc.returncode == 0
    # The summary is shown, not the 6000-char blob.
    assert "[Lensify]" in proc.stdout
    assert "x" * 6000 not in proc.stdout
    # Raw is preserved on disk under the cache dir.
    assert list((tmp_path / ".lensify-outputs").glob("*.txt"))


def test_small_output_passes_through(tmp_path):
    proc = run(["--", sys.executable, "-c", "print('hello')"], tmp_path)
    assert proc.returncode == 0
    assert "hello" in proc.stdout
    assert "[Lensify]" not in proc.stdout


def test_exit_code_is_preserved(tmp_path):
    proc = run(["--", sys.executable, "-c", "import sys; sys.exit(3)"], tmp_path)
    assert proc.returncode == 3


def test_missing_command_reports_error(tmp_path):
    proc = run(["--", "definitely-not-a-real-binary-xyz"], tmp_path)
    assert proc.returncode == 127
    assert "command not found" in proc.stderr


def test_no_command_usage(tmp_path):
    proc = run([], tmp_path)
    assert proc.returncode == 2
    assert "usage:" in proc.stderr
