"""Tests for the Phase 5 symbol extractor."""
from __future__ import annotations

import pytest

from scripts.symbols import (
    extract_python_signatures, extract_js_signatures, extract_go_signatures,
    extract_signatures, find_top_symbols, rank_files_by_imports, symbols_to_dicts,
    Symbol,
)
from scripts.walker import walk, FileRecord
from scripts.ast_parser import parse_all


def _record(path, abs_path, language="Python"):
    return FileRecord(
        path=path, abs_path=str(abs_path), extension=".py",
        language=language, is_code=True, is_doc=False, is_meta=False,
        size_bytes=0, loc=0,
    )


# ---------- Python ----------

def test_python_function_with_annotations(tmp_path):
    f = tmp_path / "auth.py"
    f.write_text(
        "from typing import Optional\n"
        "def authenticate(email: str, password: str) -> Optional[str]:\n"
        "    return None\n"
    )
    syms = extract_python_signatures(str(f), "auth.py")
    assert any(s.name == "authenticate" for s in syms)
    s = next(s for s in syms if s.name == "authenticate")
    assert "email: str" in s.signature
    assert "password: str" in s.signature
    assert "Optional[str]" in s.signature
    assert s.kind == "function"


def test_python_function_without_annotations(tmp_path):
    f = tmp_path / "u.py"
    f.write_text("def hello(name): return f'hi {name}'\n")
    syms = extract_python_signatures(str(f), "u.py")
    s = next(s for s in syms if s.name == "hello")
    assert s.signature == "hello(name)"


def test_python_class_emits_class_and_methods(tmp_path):
    f = tmp_path / "svc.py"
    f.write_text(
        "class UserService:\n"
        "    def find_by_email(self, email: str) -> dict:\n"
        "        return {}\n"
        "    def create(self, payload: dict) -> int:\n"
        "        return 0\n"
    )
    syms = extract_python_signatures(str(f), "svc.py")
    names = {s.name for s in syms}
    assert "UserService" in names
    assert "UserService.find_by_email" in names
    assert "UserService.create" in names
    method = next(s for s in syms if s.name == "UserService.find_by_email")
    assert "email: str" in method.signature
    assert "-> dict" in method.signature
    assert method.kind == "method"


def test_python_class_with_bases(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("class Greeter(BaseHandler): pass\n")
    syms = extract_python_signatures(str(f), "m.py")
    s = next(s for s in syms if s.name == "Greeter")
    assert s.signature == "class Greeter(BaseHandler)"


def test_python_skips_private_symbols(tmp_path):
    f = tmp_path / "p.py"
    f.write_text(
        "def _internal(): pass\n"
        "def public(): pass\n"
        "class _Hidden: pass\n"
    )
    syms = extract_python_signatures(str(f), "p.py")
    names = {s.name for s in syms}
    assert "public" in names
    assert "_internal" not in names
    assert "_Hidden" not in names


def test_python_handles_syntax_errors_safely(tmp_path):
    f = tmp_path / "broken.py"
    f.write_text("def f(\n  not valid\n")
    syms = extract_python_signatures(str(f), "broken.py")
    assert syms == []


def test_python_kwargs_and_varargs(tmp_path):
    f = tmp_path / "v.py"
    f.write_text("def fn(a, *args, **kwargs): pass\n")
    syms = extract_python_signatures(str(f), "v.py")
    s = next(s for s in syms if s.name == "fn")
    assert "*args" in s.signature
    assert "**kwargs" in s.signature


def test_python_async_function(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("async def fetch(url: str) -> bytes:\n    return b''\n")
    syms = extract_python_signatures(str(f), "a.py")
    s = next(s for s in syms if s.name == "fetch")
    assert "url: str" in s.signature
    assert "-> bytes" in s.signature


# ---------- JavaScript / TypeScript ----------

def test_js_function_declaration(tmp_path):
    f = tmp_path / "h.ts"
    f.write_text(
        "export function login(email: string, pw: string): Promise<Token> { return null; }\n"
    )
    syms = extract_js_signatures(str(f), "h.ts")
    s = next(s for s in syms if s.name == "login")
    assert "email: string" in s.signature
    assert "pw: string" in s.signature


def test_js_class(tmp_path):
    f = tmp_path / "c.ts"
    f.write_text("export class UserCtl extends BaseCtl {}\n")
    syms = extract_js_signatures(str(f), "c.ts")
    s = next(s for s in syms if s.name == "UserCtl")
    assert "extends BaseCtl" in s.signature


def test_js_arrow_function(tmp_path):
    f = tmp_path / "x.ts"
    f.write_text("export const handle = (req, res) => { return res.send('ok'); };\n")
    syms = extract_js_signatures(str(f), "x.ts")
    s = next(s for s in syms if s.name == "handle")
    assert "req, res" in s.signature


# ---------- Go ----------

def test_go_top_level_func(tmp_path):
    f = tmp_path / "main.go"
    f.write_text("package main\nfunc Hello(name string) string {\n  return name\n}\n")
    syms = extract_go_signatures(str(f), "main.go")
    s = next(s for s in syms if s.name == "Hello")
    assert "name string" in s.signature


def test_go_method_with_receiver(tmp_path):
    f = tmp_path / "svc.go"
    f.write_text(
        "package svc\n"
        "func (s *Service) Find(id int) (*User, error) {\n"
        "  return nil, nil\n"
        "}\n"
    )
    syms = extract_go_signatures(str(f), "svc.go")
    s = next(s for s in syms if s.name == "Service.Find")
    assert "id int" in s.signature
    assert s.kind == "method"


def test_go_struct_and_interface(tmp_path):
    f = tmp_path / "t.go"
    f.write_text("package t\ntype Token struct {}\ntype Service interface {}\n")
    syms = extract_go_signatures(str(f), "t.go")
    names = {s.name for s in syms}
    assert "Token" in names
    assert "Service" in names


def test_go_skips_lowercase_unexported(tmp_path):
    f = tmp_path / "u.go"
    f.write_text("package u\nfunc internal() {}\nfunc Public() {}\n")
    syms = extract_go_signatures(str(f), "u.go")
    names = {s.name for s in syms}
    assert "Public" in names
    assert "internal" not in names


# ---------- Dispatcher ----------

def test_extract_signatures_dispatches_by_language(tmp_path):
    py = tmp_path / "x.py"
    py.write_text("def f(): pass\n")
    rec_py = _record("x.py", py, "Python")
    assert any(s.name == "f" for s in extract_signatures(rec_py))


def test_extract_signatures_returns_empty_for_unknown_language(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("not code\n")
    rec = _record("x.txt", f, language=None)
    rec.is_code = False
    assert extract_signatures(rec) == []


# ---------- Ranking + top-N selection ----------

def test_rank_files_by_imports(tmp_path):
    # Build a tiny project: db.py imported by 3 files, util.py imported by 1
    (tmp_path / "db.py").write_text("def get(): pass\n")
    (tmp_path / "util.py").write_text("def x(): pass\n")
    (tmp_path / "a.py").write_text("import db\nimport util\n")
    (tmp_path / "b.py").write_text("import db\n")
    (tmp_path / "c.py").write_text("import db\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    scores = rank_files_by_imports(parsed)
    db_score = scores["db.py"]
    util_score = scores["util.py"]
    assert db_score > util_score


def test_find_top_symbols_returns_signatures(tmp_path):
    (tmp_path / "auth.py").write_text(
        "def authenticate(email, pw):\n    return 'tok'\n"
        "def logout():\n    return None\n"
    )
    (tmp_path / "main.py").write_text(
        "from auth import authenticate, logout\n"
        "def run(): authenticate('a', 'b')\n"
    )
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    syms = find_top_symbols(result.code_files, parsed, top_n=10)
    names = {s.name for s in syms}
    assert "authenticate" in names
    assert "logout" in names


def test_find_top_symbols_respects_top_n(tmp_path):
    # Many symbols, cap at 3
    src = "\n".join(f"def f_{i}(): pass" for i in range(20))
    (tmp_path / "m.py").write_text(src)
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    syms = find_top_symbols(result.code_files, parsed, top_n=3)
    assert len(syms) <= 3


def test_find_top_symbols_no_duplicates(tmp_path):
    """Same symbol name in two files shouldn't appear twice."""
    (tmp_path / "a.py").write_text("def shared(): pass\n")
    (tmp_path / "b.py").write_text("def shared(): pass\n")
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    syms = find_top_symbols(result.code_files, parsed, top_n=10)
    shared = [s for s in syms if s.name == "shared"]
    assert len(shared) == 1


def test_symbols_to_dicts_serializable():
    s = Symbol(name="f", signature="f(x)", path="a.py", line=1, kind="function")
    d = symbols_to_dicts([s])
    import json
    json.dumps(d)  # should not raise


def test_find_top_symbols_empty_project(tmp_path):
    result = walk(str(tmp_path))
    parsed = parse_all(result.code_files)
    syms = find_top_symbols(result.code_files, parsed)
    assert syms == []
