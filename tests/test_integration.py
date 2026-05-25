"""End-to-end integration test: run the full scan on a fixture project."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.scan import scan


def test_scan_simple_project(simple_project, tmp_path):
    out = tmp_path / "out"
    lens_data = scan(
        str(simple_project),
        no_git=True,
        output_dir=str(out),
    )
    # Files were produced
    assert (out / "LENS.html").exists()
    assert (out / "LENS.capsule.md").exists()
    assert (out / "lens.json").exists()
    assert (out / "manifest.json").exists()

    # Lens data is well-formed
    assert lens_data["tier"] in ("T1", "T2", "T3")
    assert lens_data["files"] > 0
    assert lens_data["primary_language"]
    assert "summary" in lens_data
    assert "modules" in lens_data
    assert "version" in lens_data


def test_scan_medium_project(medium_project, tmp_path):
    out = tmp_path / "out"
    lens_data = scan(
        str(medium_project),
        no_git=True,
        output_dir=str(out),
    )
    # Medium project should hit T1 or T2 depending on fixture size
    assert lens_data["tier"] in ("T1", "T2")
    # Multi-module
    assert len(lens_data["modules"]) >= 2
    # Lens HTML contains the project name
    html = (out / "LENS.html").read_text()
    assert lens_data["project_name"] in html
    assert "<title>" in html
    assert "mermaid" in html


def test_scan_capsule_only_skips_html(simple_project, tmp_path):
    out = tmp_path / "out"
    scan(
        str(simple_project),
        no_git=True,
        capsule_only=True,
        output_dir=str(out),
    )
    assert (out / "LENS.capsule.md").exists()
    assert not (out / "LENS.html").exists()


def test_scan_tier_override(simple_project, tmp_path):
    out = tmp_path / "out"
    lens_data = scan(
        str(simple_project),
        tier_override="T3",
        no_git=True,
        output_dir=str(out),
    )
    assert lens_data["tier"] == "T3"
    assert "override" in lens_data["tier_decision"]["reason"]


def test_scan_empty_directory(tmp_path):
    out = tmp_path / "out"
    lens_data = scan(str(tmp_path), no_git=True, output_dir=str(out))
    assert lens_data["tier"] == "T1"
    assert lens_data["files"] == 0
    assert (out / "LENS.html").exists()


def test_lens_json_is_valid_json(simple_project, tmp_path):
    out = tmp_path / "out"
    scan(str(simple_project), no_git=True, output_dir=str(out))
    data = json.loads((out / "lens.json").read_text())
    assert "tier" in data
    assert "files" in data
    assert isinstance(data["modules"], list)
