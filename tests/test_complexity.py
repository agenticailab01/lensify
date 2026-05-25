"""Tests for complexity tier detection."""
from __future__ import annotations

import pytest

from scripts.walker import walk
from scripts.complexity import decide, TIER_BUDGETS


def test_t1_small_project(tmp_path):
    """A trivial single-language project picks T1."""
    (tmp_path / "main.py").write_text("def hello():\n    print('hi')\n")
    (tmp_path / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.tier == "T1"
    assert decision.primary_language == "Python"
    assert decision.files == 2


def test_t2_medium_project(tmp_path):
    """Multi-module project with > 50 files picks T2."""
    for mod in ("api", "domain", "db"):
        d = tmp_path / mod
        d.mkdir()
        for i in range(20):
            (d / f"file_{i}.py").write_text("def f():\n    pass\n" * 5)
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.tier == "T2"
    assert "api" in decision.top_dirs
    assert "domain" in decision.top_dirs


def test_t3_monorepo_picks_t3(tmp_path):
    """Monorepo marker file forces T3."""
    (tmp_path / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n")
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "a").mkdir()
    (tmp_path / "packages" / "a" / "index.ts").write_text("export const x = 1;\n")
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.tier == "T3"
    assert "pnpm-workspace.yaml" in decision.monorepo_markers


def test_t3_many_files(tmp_path):
    """A project with > 1000 files is T3 even without monorepo markers."""
    for i in range(1100):
        (tmp_path / f"f_{i}.py").write_text("x = 1\n")
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.tier == "T3"


def test_tier_override_honored(tmp_path):
    (tmp_path / "a.py").write_text("x=1\n")
    result = walk(str(tmp_path))
    decision = decide(result, override="T3")
    assert decision.tier == "T3"
    assert "override" in decision.reason


def test_decision_reason_is_informative(tmp_path):
    (tmp_path / "a.py").write_text("x=1\n")
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.reason  # non-empty
    assert isinstance(decision.reason, str)


def test_tier_budgets_well_formed():
    for tier in ("T1", "T2", "T3"):
        b = TIER_BUDGETS[tier]
        assert b["total"] > 0
        section_sum = sum(v for k, v in b.items() if k != "total")
        # Total should be ≥ sum of sections (or close) — sections are SOFT caps
        assert section_sum <= b["total"] * 1.1


def test_decide_handles_empty_project(tmp_path):
    """Empty directory should still produce a decision (T1)."""
    result = walk(str(tmp_path))
    decision = decide(result)
    assert decision.tier == "T1"
    assert decision.files == 0


def test_polyglot_project(tmp_path):
    """Project with two roughly equal languages."""
    for i in range(5):
        (tmp_path / f"a_{i}.py").write_text("x=1\n" * 10)
        (tmp_path / f"b_{i}.ts").write_text("const x=1;\n" * 10)
    result = walk(str(tmp_path))
    decision = decide(result)
    # Should not be T1 since primary share < 0.8
    assert decision.tier != "T1"
