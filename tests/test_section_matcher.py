"""Tests for the section matcher (Phase 3)."""
from __future__ import annotations

import pytest

from scripts.section_matcher import match, cap, MAX_SECTIONS, SECTION_KEYWORDS


def test_match_summary_keywords():
    r = match("what does this project do?")
    assert "summary" in r.sections


def test_match_entry_keywords():
    r = match("how do I run this?")
    assert "entry" in r.sections


def test_match_modules_keywords():
    r = match("where does the auth code live?")
    assert "modules" in r.sections


def test_match_conventions_keywords():
    r = match("what's the coding style?")
    assert "conventions" in r.sections


def test_match_hotspots_keywords():
    r = match("which files are changing frequently?")
    assert "hotspots" in r.sections


def test_match_risks_keywords():
    r = match("any known issues or problems?")
    assert "risks" in r.sections


def test_module_name_boosts_modules():
    """When the user mentions a known module name, MODULES should win."""
    r = match("can you find the auth module?", module_paths=["auth", "api", "db"])
    assert "modules" in r.sections
    # MODULES should score highest due to +3 boost
    assert r.sections[0] == "modules"
    assert "auth" in r.matched_modules


def test_session_indicator_sets_needs_session():
    r = match("what have we done so far in this session?")
    assert r.needs_session is True


def test_no_session_indicator_keeps_false():
    r = match("what is this project?")
    assert r.needs_session is False


def test_empty_prompt_returns_no_sections():
    r = match("")
    assert r.sections == []


def test_short_meaningless_prompt_returns_no_sections():
    r = match("hi")
    # Length is 2, below the cutoff
    assert r.sections == []


def test_unrecognised_prompt_safe_default():
    """An unrelated prompt should still get SUMMARY + MODULES as safe defaults."""
    r = match("tell me about quantum mechanics")
    # Default fallback kicks in
    assert "summary" in r.sections
    assert "modules" in r.sections


def test_cap_limits_section_count():
    # Manually build a result with many sections
    r = match("how do I run, where is the code, what's the style?")
    capped = cap(r, max_sections=2)
    assert len(capped) <= 2


def test_max_sections_default():
    # Generate a prompt that hits everything
    r = match(
        "what is this run start where module convention "
        "hot churn risk problem"
    )
    capped = cap(r)
    assert len(capped) <= MAX_SECTIONS


def test_keyword_matching_case_insensitive():
    r1 = match("WHAT IS THIS PROJECT?")
    r2 = match("what is this project?")
    assert "summary" in r1.sections
    assert "summary" in r2.sections


def test_word_boundary_avoids_false_positives():
    """`run` shouldn't match inside `running` or `truncate`."""
    r = match("debugging truncate issues")
    # `run` is inside `truncate` but should NOT match (word boundary)
    # We allow it to match `risks` via `issues` but not `entry` via `run`.
    # If `entry` is in sections, the word-boundary logic is broken.
    # (This is best-effort; we accept some imprecision.)
    assert "entry" not in r.sections or r.scores["entry"] == 0


def test_module_path_with_subdir(monkeypatch):
    """Module paths like 'api/v2' should match 'api'."""
    r = match("where is the api?", module_paths=["api/v2", "domain"])
    assert "modules" in r.sections


def test_section_keywords_well_formed():
    """Each section has at least one keyword."""
    for section, kws in SECTION_KEYWORDS.items():
        assert kws, f"section {section} has no keywords"
