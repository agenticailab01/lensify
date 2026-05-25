"""Tests for the AST/regex parser."""
from __future__ import annotations

import pytest

from scripts.walker import walk, FileRecord
from scripts.ast_parser import (
    parse_python, parse_javascript, parse_go, parse_all,
    detect_entry_points, detect_shape, parse_file,
)


def _record(path, abs_path, language):
    return FileRecord(
        path=path, abs_path=str(abs_path), extension="."+language.lower(),
        language=language, is_code=True, is_doc=False, is_meta=False,
        size_bytes=0, loc=0,
    )


def test_python_imports_classes_functions(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(
        '"""Module docstring."""\n'
        "import os\n"
        "from collections import defaultdict\n"
        "class Greeter:\n    pass\n"
        "def hello():\n    pass\n"
        "def _private():\n    pass\n"
    )
    r = _record("m.py", f, "Python")
    p = parse_python(r)
    assert "os" in p.imports
    assert "collections" in p.imports
    assert "Greeter" in p.classes
    assert "hello" in p.functions
    assert "_private" not in p.functions
    assert p.docstring and "docstring" in p.docstring.lower()


def test_python_syntax_error_is_safe(tmp_path):
    """Broken Python should not crash the parser."""
    f = tmp_path / "broken.py"
    f.write_text("def oops(\n    this is not valid\n")
    r = _record("broken.py", f, "Python")
    p = parse_python(r)
    assert p.path == "broken.py"
    assert p.classes == []
    assert p.functions == []


def test_javascript_imports(tmp_path):
    f = tmp_path / "app.ts"
    f.write_text(
        "import React from 'react';\n"
        "import { useState } from 'react';\n"
        "const fs = require('fs');\n"
        "export class Foo {}\n"
        "export function bar() {}\n"
        "export const baz = 1;\n"
    )
    r = _record("app.ts", f, "TypeScript")
    p = parse_javascript(r)
    assert "react" in p.imports
    assert "fs" in p.imports
    assert "Foo" in p.classes
    assert "bar" in p.functions
    assert "baz" in p.exports


def test_go_imports(tmp_path):
    f = tmp_path / "main.go"
    f.write_text(
        'package main\n'
        'import "fmt"\n'
        'import (\n  "os"\n  "net/http"\n)\n'
        "func Hello() {}\n"
        "type User struct { ID int }\n"
    )
    r = _record("main.go", f, "Go")
    p = parse_go(r)
    assert "fmt" in p.imports
    assert "os" in p.imports
    assert "http" in p.imports
    assert "Hello" in p.functions
    assert "User" in p.classes


def test_parse_all_skips_non_code(tmp_path):
    """parse_all should only process code files."""
    (tmp_path / "code.py").write_text("def f(): pass\n")
    (tmp_path / "README.md").write_text("# Docs\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    assert len(parsed) == 1
    assert parsed[0].path == "code.py"


def test_detect_entry_points_python(tmp_path):
    (tmp_path / "main.py").write_text("def main(): pass\n")
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "util.py").write_text("def helper(): pass\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    entries = detect_entry_points(parsed)
    paths = [e["path"] for e in entries]
    assert "main.py" in paths
    assert "app.py" in paths
    assert "util.py" not in paths


def test_shape_layered_detected(tmp_path):
    for d in ("api", "domain", "db"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "f.py").write_text("def f(): pass\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    shape = detect_shape(parsed, ["api", "domain", "db"])
    assert shape["shape"] == "layered"


def test_shape_pipeline_detected(tmp_path):
    for d in ("ingest", "transform", "load"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "f.py").write_text("def f(): pass\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    shape = detect_shape(parsed, ["ingest", "transform", "load"])
    assert shape["shape"] == "pipeline"


def test_shape_fallback_for_unknown(tmp_path):
    (tmp_path / "random").mkdir()
    (tmp_path / "random" / "f.py").write_text("def f(): pass\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    shape = detect_shape(parsed, ["random"])
    assert shape["shape"] in ("flat", "hub-spoke")
    assert shape["confidence"] in ("forced", "weak")


def test_parse_file_dispatcher(tmp_path):
    """parse_file should dispatch to the right language parser."""
    f = tmp_path / "x.py"
    f.write_text("def x(): pass\n")
    r = _record("x.py", f, "Python")
    p = parse_file(r)
    assert p.language == "Python"
    assert "x" in p.functions
