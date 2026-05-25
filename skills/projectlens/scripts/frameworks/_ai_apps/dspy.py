"""DSPy adapter — surfaces Signatures, Modules, predictors, optimizers.

Triggers on `dspy` imports. Extracts the four building blocks of a DSPy
program:

    - Signature classes (declare input/output schema for a step)
    - Module subclasses (compose multiple predictors)
    - Predictor assignments: Predict, ChainOfThought, ReAct, ProgramOfThought
    - settings.configure() / optimizers (BootstrapFewShot, MIPROv2, …)

Output: ## DSPY capsule section.
"""
from __future__ import annotations

import re

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


_SIG_RE = re.compile(r"""class\s+(\w+)\s*\(\s*(?:dspy\.)?Signature\s*\)""")
_MOD_RE = re.compile(r"""class\s+(\w+)\s*\(\s*(?:dspy\.)?Module\s*\)""")
_PREDICT_RE = re.compile(
    r"""(\w+)\s*=\s*dspy\.(Predict|ChainOfThought|ReAct|ProgramOfThought|MultiChainComparison)\s*\("""
)
_OPTIMIZER_RE = re.compile(
    r"""(\w+)\s*=\s*(?:dspy\.)?(BootstrapFewShot|BootstrapFewShotWithRandomSearch|"""
    r"""MIPROv2|MIPRO|COPRO|KNNFewShot|Ensemble)\s*\("""
)
_CONFIGURE_RE = re.compile(r"""dspy\s*\.\s*settings\s*\.\s*configure\s*\(""")


class DSPyAdapter(FrameworkAdapter):
    name = "dspy"
    detect_signatures = ("import dspy", "from dspy")
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["dspy"]

        entries: list[FrameworkEntry] = []
        configured = False
        configure_loc = ""

        for rel_path, text in iter_python_with(parsed_files, walk_result, "dspy"):
            for m in _SIG_RE.finditer(text):
                entries.append(_entry("signature", m.group(1), "Signature",
                                      rel_path, line_of(text, m.start())))
            for m in _MOD_RE.finditer(text):
                entries.append(_entry("module", m.group(1), "Module",
                                      rel_path, line_of(text, m.start())))
            for m in _PREDICT_RE.finditer(text):
                entries.append(_entry("predictor", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _OPTIMIZER_RE.finditer(text):
                entries.append(_entry("optimizer", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            cm = _CONFIGURE_RE.search(text)
            if cm and not configured:
                configured = True
                configure_loc = f"{rel_path}:{line_of(text, cm.start())}"

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["configured"] = configured
        info.meta["configure_loc"] = configure_loc
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("configured"):
            return None
        lines = ["## DSPY"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        if info.meta.get("configured"):
            lines.append(f"- settings.configure() at {info.meta.get('configure_loc')}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": cls},
    )
