"""Git churn analyzer for hotspot detection.

Hotspots = files with the most commits over the last N days. The intuition:
files that change often are where bugs hide, features grow, and onboarding pain
concentrates. We surface them so the lens reader knows where to focus.

Pure stdlib + subprocess. No GitPython dependency.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hotspot:
    path: str        # relative path
    commits: int     # commit count in window
    authors: int     # distinct authors in window
    last_touched: str  # ISO date of most recent change

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "commits": self.commits,
            "authors": self.authors,
            "last_touched": self.last_touched,
        }


def is_git_repo(root: str | Path) -> bool:
    """Cheap check: does a .git directory or file exist at the root?"""
    p = Path(root) / ".git"
    return p.exists()


def _run_git(args: list[str], cwd: str) -> str:
    """Run a git command, return stdout or empty string on failure."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return ""
        return proc.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def analyze_hotspots(root: str, days: int = 90, top: int = 10) -> list[Hotspot]:
    """Return the top-N hotspot files by commit count in the last `days` days.

    Robust to:
        - Repos without git installed
        - Brand-new repos (no commits yet)
        - File renames (we attribute to the current path)
    """
    if not is_git_repo(root):
        return []

    # Get one line per commit, with the date and changed files
    since = f"--since={days}.days.ago"
    log = _run_git(
        ["log", since, "--name-only", "--pretty=format:%H|%aI|%ae"],
        cwd=root,
    )
    if not log:
        return []

    # Parse: blocks separated by blank lines
    commits_per_file: dict[str, int] = {}
    authors_per_file: dict[str, set[str]] = {}
    last_per_file: dict[str, str] = {}

    current_date: str | None = None
    current_author: str | None = None

    for line in log.splitlines():
        line = line.rstrip()
        if not line:
            current_date = None
            current_author = None
            continue
        if "|" in line and len(line.split("|")) == 3 and current_date is None:
            # Commit header
            _hash, date, email = line.split("|", 2)
            current_date = date
            current_author = email
            continue
        # Otherwise it's a file path
        if current_date and line:
            commits_per_file[line] = commits_per_file.get(line, 0) + 1
            authors_per_file.setdefault(line, set()).add(current_author or "?")
            prev = last_per_file.get(line)
            if not prev or current_date > prev:
                last_per_file[line] = current_date

    # Filter out files that no longer exist (renames, deletes)
    root_path = Path(root)
    hotspots: list[Hotspot] = []
    for path, count in commits_per_file.items():
        if not (root_path / path).exists():
            continue
        hotspots.append(Hotspot(
            path=path,
            commits=count,
            authors=len(authors_per_file.get(path, set())),
            last_touched=(last_per_file.get(path) or "")[:10],
        ))

    hotspots.sort(key=lambda h: h.commits, reverse=True)
    return hotspots[:top]


def churn_share(hotspots: list[Hotspot]) -> float:
    """Return the share of total commits accounted for by the top hotspots.

    Useful for the narrative line "these N files account for X% of recent
    changes." Returns 0..1.
    """
    if not hotspots:
        return 0.0
    total = sum(h.commits for h in hotspots)
    top5 = sum(h.commits for h in hotspots[:5])
    return top5 / total if total else 0.0
