"""Jupyter notebook framework adapter.

Unlike most adapters (which detect by import signature), this one triggers
purely on file presence: if any `.ipynb` file exists in the project, the
adapter activates. It surfaces a `NOTEBOOKS` section in the capsule listing
up to max_entries notebooks with their structure summary.

This addresses the single biggest gap in the AI-dev workflow: before v0.7.0,
ProjectLens IGNORED `.ipynb` entirely. Notebooks were invisible. Now an
agent asked "what's in train.ipynb?" gets the table of contents + imports +
defined functions without reading the raw 200 KB JSON.

Cell-level dedup (pointing the agent to a specific cell on re-reads) is
planned for Phase 9.1 and builds on the NotebookSummary.cells list this
adapter already produces.
"""
from __future__ import annotations

from pathlib import Path

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from .parser import parse_notebooks, NotebookSummary
except ImportError:  # script-style fallback
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from _notebooks.parser import parse_notebooks, NotebookSummary  # type: ignore[no-redef]


class JupyterAdapter(FrameworkAdapter):
    """Surfaces every `.ipynb` notebook in the project."""

    name = "jupyter"
    detect_signatures = ("ipynb",)   # placeholder — detection overridden below
    priority = PRIORITY_MEDIUM
    max_entries = 20

    # ----- Custom detection: trigger on .ipynb file presence, not imports -----

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        """O(1) — single pass over already-walked file records."""
        for rec in walk_result.files:
            if getattr(rec, "language", None) == "Jupyter":
                return True
        return False

    # ----- Extraction -----

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = [".ipynb"]

        summaries = parse_notebooks(
            [r for r in walk_result.files if getattr(r, "language", None) == "Jupyter"]
        )
        # Sort: largest LOC first (heaviest notebooks are most important to surface)
        summaries.sort(key=lambda s: s.loc, reverse=True)

        entries: list[FrameworkEntry] = []
        for s in summaries:
            entries.append(_summary_to_entry(s))

        info.entries = cap_entries(entries, self.max_entries)
        info.meta["notebooks_total"] = len(summaries)
        info.meta["notebooks_executed"] = sum(1 for s in summaries if s.executed)
        return info

    # ----- Capsule rendering -----

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## NOTEBOOKS"]
        for e in info.entries:
            meta = e.meta
            exec_tag = "executed" if meta.get("executed") else "not run"
            cells_part = (
                f"{meta.get('total_cells', 0)} cells "
                f"({meta.get('code_cells', 0)} code, {meta.get('md_cells', 0)} md)"
            )
            lines.append(f"- `{e.path}` — {cells_part} · {exec_tag}")
            imports = meta.get("imports") or []
            if imports:
                lines.append(f"  - Imports: {', '.join(imports[:8])}")
            headings = meta.get("headings") or []
            if headings:
                # Headings already have leading '#' — strip for readability
                toc = " · ".join(h.lstrip("#").strip() for h in headings[:5])
                lines.append(f"  - TOC: {toc}")
            defs = meta.get("defs") or []
            if defs:
                lines.append(f"  - Defines: {', '.join(defs[:6])}")

        out = "\n".join(lines)
        # Enforce budget via shared helper from scripts.capsule
        from importlib import import_module
        try:
            cap_mod = import_module("scripts.capsule")
        except ImportError:
            try:
                cap_mod = import_module("capsule")
            except ImportError:
                return out
        return cap_mod.truncate_to_tokens(out, budget_tokens)


def _summary_to_entry(s: NotebookSummary) -> FrameworkEntry:
    """Convert NotebookSummary into the generic FrameworkEntry envelope.

    `meta` carries notebook-specific fields the capsule renderer consumes.
    """
    confidence = "AMBIGUOUS" if s.error else "EXTRACTED"
    return FrameworkEntry(
        kind="notebook",
        name=Path(s.path).stem,
        signature=f"{s.total_cells} cells · {s.loc} LOC",
        path=s.path,
        line=0,
        confidence=confidence,
        meta={
            "total_cells": s.total_cells,
            "code_cells": s.code_cells,
            "md_cells": s.md_cells,
            "executed": s.executed,
            "loc": s.loc,
            "imports": s.imports,
            "defs": s.defs,
            "headings": s.headings,
            "largest_code_cells": s.largest_code_cells,
            "nbformat": s.nbformat,
            "error": s.error,
        },
    )
