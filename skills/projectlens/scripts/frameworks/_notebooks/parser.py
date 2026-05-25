"""Jupyter `.ipynb` parser — pure stdlib.

Extracts the parts of a notebook ProjectLens actually cares about:
    - Cell count (code / markdown / raw)
    - Total LOC across code cells (real source lines, not JSON lines)
    - Imports across code cells (deduped, sorted by frequency)
    - Function / class definitions across code cells
    - Markdown headings (notebook table of contents)
    - Executed-or-not flag (any cell has outputs?)
    - Largest code cells (where the heavy lifting concentrates)

The parser is deterministic, has no external deps, and skips notebooks
larger than MAX_NOTEBOOK_BYTES (5 MB default) — those are typically full
of embedded images, not source code worth analysing.

Separate from `jupyter.py` (the adapter) so the parsing logic can be unit-tested
in isolation and reused by future features (e.g. cell-level dedup in Phase 9.1).
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    from ...walker import MAX_NOTEBOOK_BYTES
except (ImportError, ValueError):
    try:
        from walker import MAX_NOTEBOOK_BYTES
    except ImportError:
        MAX_NOTEBOOK_BYTES = 5 * 1024 * 1024  # safe default

# Drop common output-cell noise that bloats notebooks. We don't extract
# outputs at all — only the source code.
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class NotebookCell:
    """One parsed cell. Source is the concatenated cell text — no outputs."""
    index: int                     # 0-based cell position in the notebook
    cell_type: str                 # "code" | "markdown" | "raw"
    source: str                    # joined source lines
    line_count: int                # number of source lines (== source.count("\n") + 1 if non-empty)
    has_output: bool = False       # for code cells; True if outputs[] non-empty
    char_count: int = 0            # len(source); used to find "heavy" cells

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NotebookSummary:
    """The complete structured form of one notebook."""
    path: str                      # relative POSIX path
    total_cells: int = 0
    code_cells: int = 0
    md_cells: int = 0
    raw_cells: int = 0
    executed: bool = False         # any code cell has outputs
    loc: int = 0                   # sum of code-cell source lines
    imports: list[str] = field(default_factory=list)   # top-level module imports, deduped
    defs: list[str] = field(default_factory=list)      # public function + class names
    headings: list[str] = field(default_factory=list)  # markdown headings (top 12)
    largest_code_cells: list[int] = field(default_factory=list)  # cell indices of top-3 largest
    nbformat: str | None = None    # e.g. "4.5"
    error: str | None = None       # populated when parsing failed
    cells: list[NotebookCell] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ----- Top-level entry point -----

def parse_notebook(abs_path: str, rel_path: str | None = None) -> NotebookSummary:
    """Parse a single `.ipynb` file. Never raises — errors land in summary.error."""
    rel = rel_path or abs_path
    summary = NotebookSummary(path=rel)
    p = Path(abs_path)
    if not p.exists():
        summary.error = "file_not_found"
        return summary
    try:
        size = p.stat().st_size
    except OSError as e:
        summary.error = f"stat_failed: {e}"
        return summary
    if size > MAX_NOTEBOOK_BYTES:
        summary.error = f"too_large: {size} bytes"
        return summary

    try:
        raw = p.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        summary.error = f"read_failed: {e}"
        return summary
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        summary.error = f"invalid_json: {e}"
        return summary

    if not isinstance(data, dict):
        summary.error = "not_an_object"
        return summary

    # nbformat version
    major = data.get("nbformat", 4)
    minor = data.get("nbformat_minor", 0)
    summary.nbformat = f"{major}.{minor}"

    cells_raw = data.get("cells", []) or []
    if not isinstance(cells_raw, list):
        summary.error = "cells_not_a_list"
        return summary

    # Walk cells
    all_imports: dict[str, int] = {}    # module -> count (rough popularity)
    all_defs: list[str] = []
    all_headings: list[str] = []
    code_sizes: list[tuple[int, int]] = []  # (index, char_count)

    for i, cell in enumerate(cells_raw):
        if not isinstance(cell, dict):
            continue
        cell_type = str(cell.get("cell_type", "raw"))
        src = _join_source(cell.get("source", ""))
        line_count = src.count("\n") + 1 if src else 0
        has_output = bool(cell.get("outputs"))
        char_count = len(src)

        parsed_cell = NotebookCell(
            index=i, cell_type=cell_type, source=src,
            line_count=line_count, has_output=has_output, char_count=char_count,
        )
        summary.cells.append(parsed_cell)
        summary.total_cells += 1

        if cell_type == "code":
            summary.code_cells += 1
            summary.loc += line_count
            if has_output:
                summary.executed = True
            _harvest_code(src, all_imports, all_defs)
            code_sizes.append((i, char_count))
        elif cell_type == "markdown":
            summary.md_cells += 1
            _harvest_headings(src, all_headings)
        else:
            summary.raw_cells += 1

    # Top imports by frequency, alphabetical tiebreak
    summary.imports = [
        name for name, _ in sorted(
            all_imports.items(), key=lambda kv: (-kv[1], kv[0])
        )[:20]
    ]
    # Defs: dedupe, preserve first-seen order, cap at 20
    seen = set()
    for d in all_defs:
        if d not in seen and not d.startswith("_"):
            seen.add(d)
            summary.defs.append(d)
        if len(summary.defs) >= 20:
            break
    # Headings: top 12, in order
    summary.headings = all_headings[:12]
    # Largest code cells by char count
    code_sizes.sort(key=lambda kv: kv[1], reverse=True)
    summary.largest_code_cells = [idx for idx, _ in code_sizes[:3]]
    return summary


# ----- Helpers -----

def _join_source(src) -> str:
    """Notebook `source` may be a string or list of strings."""
    if isinstance(src, str):
        return src
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return ""


def _harvest_code(source: str, imports: dict[str, int], defs: list[str]) -> None:
    """Pull imports + def/class names from a single code cell using stdlib ast.

    Best-effort: cells with syntax errors are skipped entirely (no fallback —
    we'd rather have a clean partial result than guess).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                top = n.name.split(".")[0]
                imports[top] = imports.get(top, 0) + 1
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                imports[top] = imports.get(top, 0) + 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.append(node.name)


def _harvest_headings(source: str, out: list[str]) -> None:
    """Extract Markdown ATX headings (#, ##, ###, …) preserving order."""
    for m in _HEADING_RE.finditer(source):
        depth = len(m.group(1))
        text = m.group(2).strip()
        if text:
            out.append(f"{'#' * depth} {text}"[:120])


def parse_notebooks(records) -> list[NotebookSummary]:
    """Parse every notebook in a walker FileRecord list. Skips non-Jupyter files."""
    out: list[NotebookSummary] = []
    for r in records:
        if getattr(r, "language", None) != "Jupyter":
            continue
        out.append(parse_notebook(r.abs_path, r.path))
    return out
