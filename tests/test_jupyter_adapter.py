"""Tests for the Jupyter framework adapter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._notebooks.jupyter import JupyterAdapter  # noqa: E402
from scripts.frameworks.registry import run_adapters  # noqa: E402


def _make_notebook(path: Path, *, imports=("torch", "numpy"), defs=("train",), executed=True):
    """Write a small but realistic notebook to disk."""
    body = "\n".join(f"import {imp}" for imp in imports) + "\n"
    body += "\n".join(f"def {d}(): pass" for d in defs) + "\n"
    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title\n", "## Setup"], "metadata": {}},
            {
                "cell_type": "code",
                "source": body.splitlines(keepends=True),
                "outputs": [{"output_type": "stream"}] if executed else [],
                "execution_count": 1 if executed else None,
                "metadata": {},
            },
        ],
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb))


@pytest.fixture
def project_with_notebooks(tmp_path):
    _make_notebook(tmp_path / "train.ipynb",
                   imports=("torch", "transformers"), defs=("train", "evaluate"))
    _make_notebook(tmp_path / "eda.ipynb",
                   imports=("pandas", "matplotlib"), defs=("plot_dist",), executed=False)
    return tmp_path


def test_detect_fires_when_ipynb_present(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    assert JupyterAdapter.detect(walk_result, parsed) is True


def test_detect_skips_pure_python_project(tmp_path):
    (tmp_path / "a.py").write_text("import os\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    assert JupyterAdapter.detect(walk_result, parsed) is False


def test_extract_surfaces_both_notebooks(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    names = {e.name for e in info.entries}
    assert "train" in names
    assert "eda" in names


def test_extract_meta_includes_imports_and_defs(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    train = next(e for e in info.entries if e.name == "train")
    assert "torch" in train.meta["imports"]
    assert "evaluate" in train.meta["defs"]
    assert train.meta["executed"] is True


def test_extract_executed_count(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    assert info.meta["notebooks_total"] == 2
    assert info.meta["notebooks_executed"] == 1   # only train.ipynb executed


def test_capsule_section_includes_toc_and_imports(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    section = JupyterAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "NOTEBOOKS" in section
    assert "train.ipynb" in section
    assert "Imports:" in section
    assert "TOC:" in section
    assert "Defines:" in section
    assert "executed" in section
    assert "not run" in section


def test_capsule_section_respects_budget(project_with_notebooks):
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    section = JupyterAdapter().capsule_section(info, budget_tokens=15)
    assert section is not None
    # 15 tok ≈ 50 chars (with slack); full content is much longer
    assert len(section) < 250


def test_run_adapters_picks_jupyter(project_with_notebooks):
    """End-to-end: the registry should auto-discover the Jupyter adapter."""
    walk_result = walk(str(project_with_notebooks))
    parsed = parse_all(walk_result.code_files)
    infos = run_adapters(walk_result, parsed, project_root=project_with_notebooks)
    jupyter_info = next((i for i in infos if i.name == "jupyter"), None)
    assert jupyter_info is not None
    assert len(jupyter_info.entries) == 2


def test_largest_notebook_ranked_first(tmp_path):
    """Notebooks are surfaced in LOC-desc order — heaviest first."""
    # tiny.ipynb: 1-line cell. huge.ipynb: 30-line cell.
    _make_notebook(tmp_path / "tiny.ipynb", imports=("os",), defs=("f",))
    big_body = ["import torch\n"] + [f"x{i} = {i}\n" for i in range(30)]
    nb = {
        "cells": [{"cell_type": "code", "source": big_body, "outputs": [], "metadata": {}}],
        "metadata": {}, "nbformat": 4, "nbformat_minor": 5,
    }
    (tmp_path / "huge.ipynb").write_text(json.dumps(nb))
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    # First entry should be the bigger one
    assert info.entries[0].name == "huge"


def test_max_entries_cap(tmp_path):
    """If 30 notebooks exist, only max_entries are surfaced."""
    for i in range(30):
        _make_notebook(tmp_path / f"nb_{i:02d}.ipynb", imports=("x",), defs=("f",))
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    assert len(info.entries) <= JupyterAdapter.max_entries


def test_malformed_notebook_marked_ambiguous(tmp_path):
    """A broken .ipynb still shows up in the capsule but with AMBIGUOUS confidence."""
    bad = tmp_path / "broken.ipynb"
    bad.write_text("not valid json {{")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    info = JupyterAdapter().extract(walk_result, parsed)
    assert len(info.entries) == 1
    assert info.entries[0].confidence == "AMBIGUOUS"
    assert info.entries[0].meta.get("error")


def test_walker_picks_ipynb_as_jupyter(tmp_path):
    """Walker should classify .ipynb as Jupyter language."""
    _make_notebook(tmp_path / "x.ipynb")
    walk_result = walk(str(tmp_path))
    record = next(r for r in walk_result.code_files if r.path == "x.ipynb")
    assert record.language == "Jupyter"
    assert record.is_code is True
