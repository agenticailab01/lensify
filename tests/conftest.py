"""Shared pytest fixtures and path setup."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the scripts package importable from tests.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "lensify"))


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def simple_project(fixtures_dir) -> Path:
    return fixtures_dir / "simple-project"


@pytest.fixture
def medium_project(fixtures_dir) -> Path:
    return fixtures_dir / "medium-project"


@pytest.fixture
def docs_only_project(fixtures_dir) -> Path:
    return fixtures_dir / "docs-only-project"
