"""Tests for capsule generation."""
from __future__ import annotations

import pytest

from scripts.capsule import (
    build_capsule, estimate_tokens, truncate_to_tokens, install_into,
)
from scripts.complexity import TIER_BUDGETS


SAMPLE_LENS = {
    "project_name": "test",
    "project_kind": "Python web API",
    "primary_language": "Python",
    "files": 200,
    "loc": 25_000,
    "summary": "Python web API; 200 files, 25k LOC.",
    "modules": [
        {"path": "api/", "purpose": "HTTP routes"},
        {"path": "domain/", "purpose": "business logic"},
        {"path": "db/", "purpose": "data layer"},
    ],
    "entry_points": [
        {"path": "main.py", "role": "main"},
        {"path": "manage.py", "role": "manage"},
    ],
    "hotspots": [
        {"path": "api/auth.py", "commits": 23, "last_touched": "2026-05-15"},
        {"path": "domain/user.py", "commits": 17, "last_touched": "2026-05-12"},
    ],
    "risks": [
        {"confidence": "EXTRACTED", "summary": "cyclical imports between `api` and `domain`"},
        {"confidence": "AMBIGUOUS", "summary": "thin module `legacy` (2 files)"},
    ],
    "conventions": ["Black + Ruff", "type hints required", "pytest"],
}


def test_t1_capsule_under_budget():
    capsule = build_capsule(SAMPLE_LENS, "T1")
    tokens = estimate_tokens(capsule)
    assert tokens <= TIER_BUDGETS["T1"]["total"] * 1.1, f"T1 over budget: {tokens} tok"


def test_t2_capsule_under_budget():
    capsule = build_capsule(SAMPLE_LENS, "T2")
    tokens = estimate_tokens(capsule)
    assert tokens <= TIER_BUDGETS["T2"]["total"] * 1.1, f"T2 over budget: {tokens} tok"


def test_t3_capsule_under_budget():
    capsule = build_capsule(SAMPLE_LENS, "T3")
    tokens = estimate_tokens(capsule)
    assert tokens <= TIER_BUDGETS["T3"]["total"] * 1.1, f"T3 over budget: {tokens} tok"


def test_capsule_contains_summary_always():
    """SUMMARY section must never be truncated."""
    capsule = build_capsule(SAMPLE_LENS, "T1")
    assert "# SUMMARY" in capsule
    assert "Python web API" in capsule


def test_capsule_has_markers():
    capsule = build_capsule(SAMPLE_LENS, "T2")
    assert "<!-- projectlens-begin -->" in capsule
    assert "<!-- projectlens-end -->" in capsule


def test_capsule_includes_all_sections_when_room():
    capsule = build_capsule(SAMPLE_LENS, "T2")
    for section in ("SUMMARY", "ENTRY", "MODULES", "HOTSPOTS", "RISKS", "CONVENTIONS"):
        assert f"## {section}" in capsule or f"# {section}" in capsule, f"missing {section}"


def test_estimate_tokens_basic():
    assert estimate_tokens("") == 0
    # ~7 chars → ~2 tokens
    assert 1 <= estimate_tokens("hello world") <= 5


def test_truncate_to_tokens_no_op_when_short():
    text = "short text"
    assert truncate_to_tokens(text, 100) == text


def test_truncate_to_tokens_cuts_long():
    text = "a\n" * 1000
    truncated = truncate_to_tokens(text, 50)
    assert estimate_tokens(truncated) <= 70  # some slack for the "…" trailer


def test_install_into_creates_file(tmp_path):
    target = tmp_path / "CLAUDE.md"
    capsule = build_capsule(SAMPLE_LENS, "T1")
    inserted, msg = install_into(capsule, str(target))
    assert inserted
    assert target.exists()
    assert "<!-- projectlens-begin -->" in target.read_text()


def test_install_into_replaces_existing(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text(
        "# Project notes\n\n"
        "<!-- projectlens-begin -->\nold content\n<!-- projectlens-end -->\n\n"
        "After block\n"
    )
    new_capsule = build_capsule(SAMPLE_LENS, "T1")
    inserted, msg = install_into(new_capsule, str(target))
    content = target.read_text()
    assert "old content" not in content
    assert "# SUMMARY" in content
    assert "After block" in content  # surrounding content preserved


def test_install_into_appends_when_no_existing_block(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text("# Existing notes\n\nSomething here.\n")
    capsule = build_capsule(SAMPLE_LENS, "T1")
    inserted, msg = install_into(capsule, str(target))
    content = target.read_text()
    assert "Existing notes" in content
    assert "<!-- projectlens-begin -->" in content


def test_unknown_tier_rejected():
    with pytest.raises(ValueError):
        build_capsule(SAMPLE_LENS, "T9")
