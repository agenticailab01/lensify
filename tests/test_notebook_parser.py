"""Tests for the Jupyter notebook parser."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.frameworks._notebooks.parser import (  # noqa: E402
    parse_notebook, parse_notebooks, NotebookSummary, NotebookCell,
)
from scripts.walker import walk  # noqa: E402


def _make_nb(cells: list[dict], nbformat=4, nbformat_minor=5) -> dict:
    """Build a minimal valid nbformat-4 notebook structure."""
    return {
        "cells": cells,
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": nbformat,
        "nbformat_minor": nbformat_minor,
    }


def _code_cell(source: list[str] | str, has_output: bool = False) -> dict:
    return {
        "cell_type": "code",
        "source": source,
        "outputs": [{"output_type": "stream"}] if has_output else [],
        "execution_count": 1 if has_output else None,
        "metadata": {},
    }


def _md_cell(source: list[str] | str) -> dict:
    return {"cell_type": "markdown", "source": source, "metadata": {}}


@pytest.fixture
def tmp_notebook(tmp_path):
    """Build a realistic 5-cell notebook on disk."""
    nb = _make_nb([
        _md_cell(["# Data Loading\n\n", "Loads MNIST."]),
        _code_cell([
            "import torch\n",
            "from torch import nn\n",
            "import torchvision\n",
        ]),
        _md_cell(["## Model"]),
        _code_cell([
            "class MyModel(nn.Module):\n",
            "    def __init__(self):\n",
            "        super().__init__()\n",
            "    def forward(self, x):\n",
            "        return x\n",
        ], has_output=False),
        _code_cell([
            "def train(model, data):\n",
            "    pass\n",
        ], has_output=True),
    ])
    path = tmp_path / "train.ipynb"
    path.write_text(json.dumps(nb))
    return path


def test_parse_basic_cell_counts(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert s.total_cells == 5
    assert s.code_cells == 3
    assert s.md_cells == 2
    assert s.raw_cells == 0
    assert s.error is None


def test_parse_executed_flag(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert s.executed is True  # last cell has output


def test_parse_imports(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert "torch" in s.imports
    assert "torchvision" in s.imports


def test_parse_defs(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert "MyModel" in s.defs
    assert "train" in s.defs


def test_parse_headings(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert any("Data Loading" in h for h in s.headings)
    assert any("Model" in h for h in s.headings)


def test_parse_loc_counts_code_lines(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    # 3 code cells with 3 + 5 + 2 = 10 lines (+ newlines)
    assert s.loc >= 10


def test_parse_largest_cells_returns_indices(tmp_notebook):
    s = parse_notebook(str(tmp_notebook), "train.ipynb")
    assert len(s.largest_code_cells) <= 3
    assert all(isinstance(i, int) for i in s.largest_code_cells)


def test_parse_handles_missing_file(tmp_path):
    s = parse_notebook(str(tmp_path / "nope.ipynb"))
    assert s.error == "file_not_found"
    assert s.total_cells == 0


def test_parse_handles_invalid_json(tmp_path):
    path = tmp_path / "broken.ipynb"
    path.write_text("not json {{")
    s = parse_notebook(str(path))
    assert s.error is not None
    assert "invalid_json" in s.error


def test_parse_handles_non_object(tmp_path):
    path = tmp_path / "wrong_shape.ipynb"
    path.write_text("[1, 2, 3]")
    s = parse_notebook(str(path))
    assert s.error == "not_an_object"


def test_parse_handles_cells_not_a_list(tmp_path):
    path = tmp_path / "cells_wrong.ipynb"
    path.write_text(json.dumps({"cells": "oops", "nbformat": 4}))
    s = parse_notebook(str(path))
    assert s.error == "cells_not_a_list"


def test_parse_handles_syntax_error_in_cell(tmp_path):
    """A code cell with broken Python should be skipped, not crash the parse."""
    nb = _make_nb([
        _code_cell("def good(): pass\n"),
        _code_cell("def bad(\n  this is wrong\n"),  # syntax error
        _code_cell("def alsoGood(): pass\n"),
    ])
    path = tmp_path / "mixed.ipynb"
    path.write_text(json.dumps(nb))
    s = parse_notebook(str(path))
    assert s.error is None
    # good and alsoGood survived; bad was skipped
    assert "good" in s.defs
    assert "alsoGood" in s.defs


def test_parse_empty_notebook(tmp_path):
    path = tmp_path / "empty.ipynb"
    path.write_text(json.dumps(_make_nb([])))
    s = parse_notebook(str(path))
    assert s.error is None
    assert s.total_cells == 0
    assert s.imports == []


def test_parse_source_as_string_works(tmp_path):
    """Some notebooks store 'source' as a single string, not a list."""
    nb = _make_nb([{
        "cell_type": "code",
        "source": "import numpy as np\ndef f(): pass\n",
        "outputs": [],
        "metadata": {},
    }])
    path = tmp_path / "str_source.ipynb"
    path.write_text(json.dumps(nb))
    s = parse_notebook(str(path))
    assert "numpy" in s.imports
    assert "f" in s.defs


def test_parse_skips_huge_files(tmp_path, monkeypatch):
    """Notebooks bigger than MAX_NOTEBOOK_BYTES are skipped without parsing."""
    # Monkeypatch the cap to something tiny
    from scripts.frameworks._notebooks import parser as p
    monkeypatch.setattr(p, "MAX_NOTEBOOK_BYTES", 100)
    nb = _make_nb([_code_cell("import x\n") for _ in range(50)])
    path = tmp_path / "big.ipynb"
    path.write_text(json.dumps(nb))
    s = parse_notebook(str(path))
    assert s.error is not None
    assert "too_large" in s.error


def test_parse_imports_deduped_and_sorted_by_frequency(tmp_path):
    """torch appears in 3 cells, numpy in 1 — torch should rank first."""
    nb = _make_nb([
        _code_cell("import torch\n"),
        _code_cell("import torch\nimport numpy\n"),
        _code_cell("import torch\n"),
    ])
    path = tmp_path / "freq.ipynb"
    path.write_text(json.dumps(nb))
    s = parse_notebook(str(path))
    assert s.imports[0] == "torch"
    assert "numpy" in s.imports


def test_parse_skips_private_defs(tmp_path):
    nb = _make_nb([_code_cell("def _internal(): pass\ndef public(): pass\n")])
    path = tmp_path / "vis.ipynb"
    path.write_text(json.dumps(nb))
    s = parse_notebook(str(path))
    assert "public" in s.defs
    assert "_internal" not in s.defs


# ---- Bulk parser via walker ----

def test_parse_notebooks_via_walker(tmp_path):
    """parse_notebooks() should pick up every .ipynb under a walked tree."""
    nb = _make_nb([_code_cell("import torch\n")])
    (tmp_path / "a.ipynb").write_text(json.dumps(nb))
    (tmp_path / "b.ipynb").write_text(json.dumps(nb))
    (tmp_path / "x.py").write_text("def x(): pass\n")  # should be ignored
    walk_result = walk(str(tmp_path))
    summaries = parse_notebooks(walk_result.code_files)
    paths = {s.path for s in summaries}
    assert "a.ipynb" in paths
    assert "b.ipynb" in paths
    assert all(s.error is None for s in summaries)
