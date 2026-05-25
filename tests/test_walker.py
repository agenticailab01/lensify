"""Tests for the directory walker."""
from __future__ import annotations

import os
import pytest

from scripts.walker import (
    walk, parse_gitignore, matches_pattern, classify_file,
    LANGUAGE_MAP, DEFAULT_EXCLUDES,
)


def test_walks_simple_project(simple_project):
    result = walk(str(simple_project))
    assert result.code_files, "should find at least one code file"
    assert all(f.is_code for f in result.code_files)


def test_excludes_node_modules(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("export {}\n")
    result = walk(str(tmp_path))
    paths = [f.path for f in result.code_files]
    assert "src/main.py" in paths
    assert not any("node_modules" in p for p in paths)


def test_respects_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("build/\n*.log\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "out.py").write_text("x = 2\n")
    (tmp_path / "debug.log").write_text("noise\n")
    result = walk(str(tmp_path))
    paths = [f.path for f in result.code_files]
    assert "src/app.py" in paths
    assert not any(p.startswith("build/") for p in paths)


def test_language_detection(tmp_path):
    samples = {
        "a.py": "Python", "b.ts": "TypeScript", "c.go": "Go",
        "d.rs": "Rust", "e.java": "Java", "f.js": "JavaScript",
    }
    for name, lang in samples.items():
        (tmp_path / name).write_text(f"// {lang}\n")
    result = walk(str(tmp_path))
    found = {f.path: f.language for f in result.code_files}
    for name, lang in samples.items():
        assert found.get(name) == lang


def test_loc_counting(tmp_path):
    (tmp_path / "f.py").write_text("a\nb\nc\nd\n")
    result = walk(str(tmp_path))
    code = result.code_files[0]
    assert code.loc == 4


def test_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        walk("/nonexistent/path/that/does/not/exist")


def test_gitignore_parser(tmp_path):
    (tmp_path / ".gitignore").write_text("# comment\n\nfoo/\n*.tmp\n!important.tmp\n")
    patterns = parse_gitignore(tmp_path)
    assert "foo" in patterns
    assert "*.tmp" in patterns
    assert "important.tmp" not in patterns  # negation ignored
    assert "" not in patterns


def test_matches_pattern():
    assert matches_pattern("src/foo.log", ["*.log"])
    assert matches_pattern("build/x.py", ["build"])
    assert not matches_pattern("src/main.py", ["dist"])


def test_default_excludes_includes_common_vendor():
    for d in ("node_modules", "vendor", "__pycache__", ".git"):
        assert d in DEFAULT_EXCLUDES


def test_language_map_coverage():
    for ext in (".py", ".js", ".ts", ".go", ".rs", ".java", ".rb"):
        assert ext in LANGUAGE_MAP
