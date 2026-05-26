"""Tests for the FastAPI reference adapter."""
from __future__ import annotations

from pathlib import Path

import pytest

import sys
SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._enterprise.fastapi import FastAPIAdapter  # noqa: E402


@pytest.fixture
def fastapi_project(tmp_path):
    (tmp_path / "main.py").write_text(
        "from fastapi import FastAPI, APIRouter\n"
        "app = FastAPI()\n"
        "router = APIRouter(prefix='/v1')\n"
        "\n"
        '@app.get("/users")\n'
        "def list_users(): pass\n"
        "\n"
        '@app.post("/users", response_model=dict)\n'
        "def create_user(): pass\n"
        "\n"
        '@router.delete("/items/{id}")\n'
        "def delete_item(id: int): pass\n"
        "\n"
        '@app.api_route("/legacy", methods=["GET", "POST"])\n'
        "def legacy(): pass\n"
    )
    return tmp_path


def test_detect_fires_on_fastapi_import(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    assert FastAPIAdapter.detect(walk_result, parsed) is True


def test_detect_skips_unrelated_project(tmp_path):
    (tmp_path / "x.py").write_text("import os\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    assert FastAPIAdapter.detect(walk_result, parsed) is False


def test_extract_finds_all_routes(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    methods = {e.meta.get("method") for e in info.entries}
    paths = {e.meta.get("path") for e in info.entries}
    assert "GET" in methods
    assert "POST" in methods
    assert "DELETE" in methods
    assert "/users" in paths
    assert "/items/{id}" in paths
    assert "/legacy" in paths


def test_extract_expands_api_route_methods(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    legacy = [e for e in info.entries if e.meta.get("path") == "/legacy"]
    methods = {e.meta.get("method") for e in legacy}
    assert "GET" in methods
    assert "POST" in methods


def test_extract_records_line_numbers(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    for e in info.entries:
        assert e.line > 0


def test_capsule_section_includes_methods(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    section = FastAPIAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "ROUTES" in section
    assert "GET /users" in section
    assert "POST /users" in section


def test_capsule_section_respects_budget(fastapi_project):
    walk_result = walk(str(fastapi_project))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    # Tiny budget should still produce *something* but truncated
    section = FastAPIAdapter().capsule_section(info, budget_tokens=20)
    assert section is not None
    # 20 tok ≈ 70 chars; full section is longer
    assert len(section) < 400


def test_extract_skips_non_python_files(tmp_path):
    (tmp_path / "a.py").write_text("from fastapi import FastAPI\napp=FastAPI()\n@app.get('/x')\ndef f(): pass\n")
    (tmp_path / "b.ts").write_text("@app.get('/from-ts')\nfunction f() {}\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    info = FastAPIAdapter().extract(walk_result, parsed)
    paths = [e.meta.get("path") for e in info.entries]
    assert "/x" in paths
    assert "/from-ts" not in paths
