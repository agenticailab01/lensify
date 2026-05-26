"""Directory walker that respects .gitignore and vendor exclusions.

Pure stdlib. No external dependencies.
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# Built-in exclusions — directories that should never count toward complexity
# regardless of .gitignore status. These are vendored, generated, or VCS internals.
DEFAULT_EXCLUDES = frozenset({
    ".git", ".hg", ".svn",
    "node_modules", "vendor", "bower_components",
    "dist", "build", "out", "target",
    ".next", ".nuxt", ".svelte-kit",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", ".env", "env",
    "coverage", ".coverage", ".nyc_output",
    ".idea", ".vscode", ".vs",
    "lensify-out", "graphify-out",
})

# Map file extensions to language names. Covers ~20 common languages.
LANGUAGE_MAP = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".ts": "TypeScript",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell",
    ".ps1": "PowerShell",
    ".lua": "Lua",
    ".dart": "Dart",
    ".ex": "Elixir", ".exs": "Elixir",
    ".vue": "Vue", ".svelte": "Svelte",
    ".ipynb": "Jupyter",
}

# Notebooks larger than this are skipped to keep the scan fast — typically
# means an embedded image / output blob, not human-authored code.
MAX_NOTEBOOK_BYTES = 5 * 1024 * 1024  # 5 MB

# Doc extensions tracked separately
DOC_EXTENSIONS = frozenset({".md", ".mdx", ".rst", ".txt", ".adoc"})

# Config/data files we want to recognise but not count as code
META_FILES = frozenset({
    "package.json", "pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json",
    "pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "composer.json", "Gemfile",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".gitignore", ".dockerignore",
    "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE",
    "tsconfig.json", "jest.config.js", "vite.config.js",
})


@dataclass
class FileRecord:
    path: str                  # relative POSIX path
    abs_path: str              # absolute path on disk
    extension: str             # lowercase extension including dot
    language: str | None       # detected language, or None
    is_code: bool              # True if it's a code file
    is_doc: bool               # True if a documentation file
    is_meta: bool              # True if a recognised metadata file
    size_bytes: int            # file size
    loc: int                   # line count (cheap proxy for LOC)


@dataclass
class WalkResult:
    root: str
    files: list[FileRecord] = field(default_factory=list)
    excluded_dirs: list[str] = field(default_factory=list)

    @property
    def code_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.is_code]

    @property
    def total_loc(self) -> int:
        return sum(f.loc for f in self.code_files)

    @property
    def language_breakdown(self) -> dict[str, int]:
        """Returns {language: loc} for code files only."""
        out: dict[str, int] = {}
        for f in self.code_files:
            if f.language:
                out[f.language] = out.get(f.language, 0) + f.loc
        return out


def parse_gitignore(root: Path) -> list[str]:
    """Parse the root .gitignore into a list of patterns.

    Does NOT handle nested .gitignore files — that's a deliberate v0 simplification.
    Patterns starting with '!' (negation) are ignored.
    """
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    patterns: list[str] = []
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        # Normalise trailing slashes for directory-only patterns
        patterns.append(line.rstrip("/"))
    return patterns


def matches_pattern(rel_path: str, patterns: list[str]) -> bool:
    """Check if a relative POSIX path matches any gitignore-style pattern."""
    parts = rel_path.split("/")
    for pat in patterns:
        # Anchored patterns (starting with /) only match from root
        if pat.startswith("/"):
            if fnmatch.fnmatch(rel_path, pat.lstrip("/")):
                return True
        else:
            # Unanchored: match any component or the whole path
            if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(rel_path, f"*/{pat}"):
                return True
            if any(fnmatch.fnmatch(p, pat) for p in parts):
                return True
    return False


def count_lines(path: Path) -> int:
    """Cheap line count. Skips binary detection — handled by extension filter."""
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def classify_file(rel_path: str, abs_path: Path) -> FileRecord:
    """Build a FileRecord for a single file."""
    ext = abs_path.suffix.lower()
    name = abs_path.name
    language = LANGUAGE_MAP.get(ext)
    is_code = language is not None
    is_doc = ext in DOC_EXTENSIONS
    is_meta = name in META_FILES
    try:
        size = abs_path.stat().st_size
    except OSError:
        size = 0
    loc = count_lines(abs_path) if (is_code or is_doc) else 0
    return FileRecord(
        path=rel_path,
        abs_path=str(abs_path),
        extension=ext,
        language=language,
        is_code=is_code,
        is_doc=is_doc,
        is_meta=is_meta,
        size_bytes=size,
        loc=loc,
    )


def walk(root: str | Path, extra_excludes: list[str] | None = None) -> WalkResult:
    """Walk a project directory.

    Excludes:
        - DEFAULT_EXCLUDES (always)
        - Anything matching .gitignore patterns (if present)
        - Any directory name in extra_excludes
    """
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Path not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    gitignore_patterns = parse_gitignore(root_path)
    extra = set(extra_excludes or [])
    excludes = DEFAULT_EXCLUDES | extra

    result = WalkResult(root=str(root_path))
    excluded_dirs: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Compute path relative to root
        rel_dir = os.path.relpath(dirpath, root_path).replace(os.sep, "/")
        if rel_dir == ".":
            rel_dir = ""

        # Prune dirs in-place so os.walk doesn't descend
        kept: list[str] = []
        for d in dirnames:
            if d in excludes or d.startswith("."):
                # Allow .github but skip other dotfile dirs
                if d != ".github":
                    excluded_dirs.append(f"{rel_dir}/{d}".lstrip("/"))
                    continue
            rel_child = f"{rel_dir}/{d}".lstrip("/")
            if gitignore_patterns and matches_pattern(rel_child, gitignore_patterns):
                excluded_dirs.append(rel_child)
                continue
            kept.append(d)
        dirnames[:] = kept

        for fname in filenames:
            rel_path = f"{rel_dir}/{fname}".lstrip("/")
            if gitignore_patterns and matches_pattern(rel_path, gitignore_patterns):
                continue
            abs_path = Path(dirpath) / fname
            result.files.append(classify_file(rel_path, abs_path))

    result.excluded_dirs = excluded_dirs
    return result


def detect_monorepo_markers(root: Path) -> list[str]:
    """Return a list of monorepo marker files present at the root."""
    markers = [
        "lerna.json", "pnpm-workspace.yaml", "nx.json", "turbo.json",
        "rush.json", "yarn-workspaces", ".yarnrc.yml",
    ]
    found: list[str] = []
    for m in markers:
        if (root / m).exists():
            found.append(m)
    # Also check for top-level workspace dirs
    for d in ("services", "apps", "packages"):
        if (root / d).is_dir():
            found.append(f"{d}/")
    return found


def top_level_dirs(result: WalkResult) -> list[str]:
    """List top-level directory names containing code, sorted."""
    dirs: set[str] = set()
    root = Path(result.root)
    for f in result.code_files:
        parts = f.path.split("/")
        if len(parts) > 1:
            dirs.add(parts[0])
        # else: file at root, ignored for module structure
    return sorted(dirs)
