"""Tests for the Phase 6 tool-output compression engine."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.output_compressor import (
    detect_output_type, compress, compress_html, compress_json, compress_log,
    compress_trace, compress_diff, compress_playwright, compress_pytest,
    compress_tabular, compress_text, format_for_agent, is_disabled,
    CompressionResult, MIN_COMPRESS_BYTES, OUTPUT_CACHE_DIRNAME,
)


# ---- Type detection ----

def test_detect_html():
    assert detect_output_type("<!DOCTYPE html>\n<html><body>hi</body></html>") == "html"
    assert detect_output_type("<html lang='en'><head></head>") == "html"


def test_detect_json_object():
    assert detect_output_type('{"a": 1, "b": [1, 2, 3]}') == "json"


def test_detect_json_array():
    assert detect_output_type('[{"id": 1}, {"id": 2}]') == "json"


def test_detect_json_invalid_falls_through():
    assert detect_output_type("{ not real json") == "text"


def test_detect_pytest():
    text = "==== test session starts ====\n.....FAILED tests/x.py::y\n==== 3 passed, 1 failed in 0.5s ===="
    assert detect_output_type(text) == "pytest"


def test_detect_playwright():
    text = "[role=button] name='Login'\n[role=textbox]\n- accessibility-tree:\n"
    assert detect_output_type(text) == "playwright"


def test_detect_log():
    lines = "\n".join(
        f"2026-05-23T10:0{i}:00 INFO request handled" for i in range(8)
    )
    assert detect_output_type(lines) == "log"


def test_detect_trace():
    text = (
        "Traceback (most recent call last):\n"
        "  File \"x.py\", line 1, in <module>\n"
        "    raise ValueError('bad')\n"
        "ValueError: bad\n"
    )
    assert detect_output_type(text) == "trace"


def test_detect_diff():
    text = (
        "diff --git a/x.py b/x.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-old\n"
        "+new\n"
    )
    assert detect_output_type(text) == "diff"


def test_detect_tabular():
    text = "name,age,role\nalice,30,eng\nbob,28,pm\ncarol,35,des\n"
    assert detect_output_type(text) == "tabular"


def test_detect_plain_text():
    assert detect_output_type("just a normal sentence with words in it.") == "text"


# ---- Compressors ----

def test_compress_html_extracts_title_headings():
    html = (
        "<html><head><title>My Page</title></head><body>"
        "<h1>Welcome</h1><h2>Features</h2><p>Lorem ipsum dolor sit amet.</p>"
        "</body></html>"
    )
    out = compress_html(html)
    assert "My Page" in out
    assert "Welcome" in out
    assert "Features" in out
    assert "Lorem ipsum" in out


def test_compress_json_schema_summary():
    data = json.dumps({"name": "x", "items": [{"id": 1}, {"id": 2}], "nested": {"a": 1}})
    out = compress_json(data)
    assert "schema" in out.lower()
    assert "name" in out or "items" in out


def test_compress_json_array_counts():
    data = json.dumps([{"id": i} for i in range(50)])
    out = compress_json(data)
    assert "50 items" in out


def test_compress_log_groups_levels():
    lines = []
    for _ in range(10):
        lines.append("2026-05-23 INFO ok")
    for _ in range(3):
        lines.append("2026-05-23 ERROR boom: connection refused")
    text = "\n".join(lines)
    out = compress_log(text)
    assert "INFO=10" in out
    assert "ERROR=3" in out
    assert "connection refused" in out


def test_compress_trace_extracts_error():
    text = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 12, in main\n'
        "    raise RuntimeError('boom')\n"
        "RuntimeError: boom\n"
    )
    out = compress_trace(text)
    assert "RuntimeError" in out
    assert "x.py" in out


def test_compress_diff_per_file_counts():
    text = (
        "diff --git a/foo.py b/foo.py\n"
        "@@ -1,2 +1,3 @@\n"
        "-a\n"
        "-b\n"
        "+x\n"
        "+y\n"
        "+z\n"
        "diff --git a/bar.py b/bar.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )
    out = compress_diff(text)
    assert "2 files" in out
    assert "foo.py" in out and "+3" in out and "-2" in out
    assert "bar.py" in out


def test_compress_playwright_roles():
    text = (
        "title='Login Page'\n"
        "[role=button] name='Submit'\n"
        "[role=button] name='Cancel'\n"
        "[role=textbox] name='email'\n"
    )
    out = compress_playwright(text)
    assert "button×2" in out or "button×" in out
    assert "Login Page" in out


def test_compress_pytest_totals_and_failures():
    text = (
        "==== test session starts ====\n"
        "FAILED tests/test_a.py::test_one\n"
        "FAILED tests/test_b.py::test_two\n"
        "==== 5 passed, 2 failed in 0.4s ===="
    )
    out = compress_pytest(text)
    assert "5 passed" in out
    assert "2 failed" in out
    assert "test_one" in out


def test_compress_tabular_keeps_header():
    text = "a,b,c\n1,2,3\n4,5,6\n7,8,9\n"
    out = compress_tabular(text)
    assert "Header: a,b,c" in out
    assert "4 rows" in out


def test_compress_text_fallback_snippets():
    text = "x" * 5000
    out = compress_text(text)
    assert "head" in out
    assert "middle" in out
    assert "tail" in out


# ---- Top-level compress() ----

def test_small_input_passes_through(tmp_path):
    text = "small output"
    result = compress(text, project_root=tmp_path)
    assert result.output_type == "passthrough"
    assert result.summary == text
    assert result.handle is None
    assert result.bytes_saved == 0


def test_large_input_compressed_and_stored(tmp_path):
    text = '{"big": ' + ",".join(f'"row_{i}"' for i in range(2000)) + ", \"end\": true}"
    # Actually generate valid JSON of >2KB
    data = {"items": [{"id": i, "name": f"name_{i}"} for i in range(200)]}
    text = json.dumps(data)
    assert len(text) > MIN_COMPRESS_BYTES
    result = compress(text, project_root=tmp_path)
    assert result.output_type == "json"
    assert result.handle is not None
    assert Path(result.handle).exists()
    assert result.bytes_saved > 0
    assert result.compressed_bytes < result.original_bytes


def test_compress_ratio_property():
    r = CompressionResult(original_bytes=1000, compressed_bytes=100,
                          output_type="text", summary="x")
    assert r.ratio == 10.0


def test_compress_storage_creates_cache_dir(tmp_path):
    text = "x" * 5000
    compress(text, project_root=tmp_path)
    assert (tmp_path / OUTPUT_CACHE_DIRNAME).exists()


def test_compress_no_store_when_disabled(tmp_path):
    text = "x" * 5000
    result = compress(text, project_root=tmp_path, store=False)
    assert result.handle is None


def test_format_for_agent_includes_size_info(tmp_path):
    text = json.dumps({"items": [{"id": i} for i in range(200)]})
    result = compress(text, project_root=tmp_path)
    out = format_for_agent(result)
    assert "ProjectLens" in out
    assert "json" in out
    assert "ratio" in out.lower()
    assert result.summary in out


def test_format_for_agent_empty_for_passthrough(tmp_path):
    text = "short"
    result = compress(text, project_root=tmp_path)
    assert format_for_agent(result) == ""


def test_is_disabled_default_false(monkeypatch):
    monkeypatch.delenv("PROJECTLENS_COMPRESS_OUTPUT", raising=False)
    monkeypatch.delenv("PROJECTLENS_DEDUP", raising=False)
    assert is_disabled() is False


def test_is_disabled_via_specific_env(monkeypatch):
    monkeypatch.setenv("PROJECTLENS_COMPRESS_OUTPUT", "0")
    assert is_disabled() is True


def test_is_disabled_via_global_env(monkeypatch):
    monkeypatch.delenv("PROJECTLENS_COMPRESS_OUTPUT", raising=False)
    monkeypatch.setenv("PROJECTLENS_DEDUP", "off")
    assert is_disabled() is True


def test_content_addressable_storage_no_duplicates(tmp_path):
    """Same input should reuse the same cache file."""
    text = json.dumps({"items": [{"id": i} for i in range(200)]})
    r1 = compress(text, project_root=tmp_path)
    r2 = compress(text, project_root=tmp_path)
    assert r1.handle == r2.handle
