"""Tests for narrative generation."""
from __future__ import annotations

from scripts.narrative import (
    template_narrative, guess_project_kind, collect_framework_hints, detect_risks,
)


def test_narrative_basic_shape():
    n = template_narrative(
        project_kind="Python web API",
        primary_language="Python",
        shape="layered",
        n_modules=4,
        hotspots=[{"path": "api/auth.py"}, {"path": "domain/user.py"}],
        churn_pct=0.6,
        risks=[{"summary": "cyclical imports exist"}],
        entry_path="main.py",
    )
    assert "Python web API" in n
    assert "layered architecture" in n
    assert "4 top-level modules" in n
    assert "auth.py" in n
    assert "60%" in n
    assert "cyclical imports" in n
    assert "main.py" in n


def test_narrative_no_hotspots_omits_section():
    n = template_narrative(
        project_kind="Go service",
        primary_language="Go",
        shape="hub-spoke",
        n_modules=2,
        hotspots=[],
        churn_pct=0.0,
        risks=[],
        entry_path=None,
    )
    assert "Go service" in n
    assert "60%" not in n
    # When no entry path, no "open ..." sentence
    assert "Open " not in n and "open " not in n


def test_project_kind_lookup():
    hints = {"fastapi"}
    kind = guess_project_kind("Python", hints)
    assert "FastAPI" in kind or "Python web API" in kind


def test_project_kind_fallback():
    kind = guess_project_kind("Lua", set())
    assert "Lua" in kind


def test_collect_framework_hints():
    modules = [{"path": "fastapi_routes/"}, {"path": "models/"}]
    entries = [{"path": "main.py", "role": "main"}]
    hints = collect_framework_hints(modules, entries)
    assert "fastapi" in hints


def test_detect_cyclical_imports():
    parsed = [
        {"path": "a/x.py", "imports": ["b"]},
        {"path": "b/y.py", "imports": ["a"]},
    ]
    modules = [{"path": "a/"}, {"path": "b/"}]
    risks = detect_risks(modules, parsed)
    assert any(r["kind"] == "cyclical_imports" for r in risks)
    cyc = next(r for r in risks if r["kind"] == "cyclical_imports")
    assert cyc["confidence"] == "EXTRACTED"


def test_detect_thin_module():
    parsed = [{"path": "tiny/only.py", "imports": []}]
    modules = [{"path": "tiny/"}]
    risks = detect_risks(modules, parsed)
    assert any(r["kind"] == "thin_module" for r in risks)
    thin = next(r for r in risks if r["kind"] == "thin_module")
    assert thin["confidence"] == "AMBIGUOUS"
