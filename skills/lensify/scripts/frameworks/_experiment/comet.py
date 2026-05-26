"""Comet ML adapter — surfaces experiments and log calls.

Triggers on `comet_ml` imports. Extracts:

    - Experiment(api_key=..., project_name=..., workspace=...) — standard
      online experiment
    - OfflineExperiment(...) — offline runs (uploaded later)
    - ExistingExperiment(...) — attach to existing run
    - .log_metric(...), .log_parameter(...), .log_parameters(...),
      .log_asset(...), .log_model(...), .log_figure(...)

Output: ## COMET capsule section.
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


# Match Experiment / OfflineExperiment / ExistingExperiment constructors —
# capture full args block, then pull project_name + workspace separately.
_EXPERIMENT_RE = re.compile(
    r"""(\w+)\s*=\s*(Experiment|OfflineExperiment|ExistingExperiment)\s*\(([^)]*)\)""",
    re.S,
)
_PROJECT_RE = re.compile(r"""project_name\s*=\s*['"]([^'"]+)['"]""")
_WORKSPACE_RE = re.compile(r"""workspace\s*=\s*['"]([^'"]+)['"]""")
_LOG_RE = re.compile(
    r"""\.\s*(log_metric|log_parameter|log_parameters|log_asset|log_model|"""
    r"""log_figure|log_image|log_table|log_text|log_html|log_curve)\s*\("""
)


class CometAdapter(FrameworkAdapter):
    name = "comet"
    detect_signatures = ("import comet_ml", "from comet_ml")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["comet_ml"]

        entries: list[FrameworkEntry] = []
        projects: set[str] = set()
        workspaces: set[str] = set()
        log_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "comet_ml"):
            for m in _EXPERIMENT_RE.finditer(text):
                var = m.group(1)
                cls = m.group(2)
                body = m.group(3) or ""
                proj = _PROJECT_RE.search(body)
                wsp = _WORKSPACE_RE.search(body)
                if proj:
                    projects.add(proj.group(1))
                if wsp:
                    workspaces.add(wsp.group(1))
                bits = []
                if proj:
                    bits.append(f"project={proj.group(1)!r}")
                if wsp:
                    bits.append(f"workspace={wsp.group(1)!r}")
                sig = f"{cls}({', '.join(bits)})" if bits else cls
                entries.append(FrameworkEntry(
                    kind="experiment",
                    name=var,
                    signature=sig,
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={
                        "class": cls,
                        "project": proj.group(1) if proj else None,
                        "workspace": wsp.group(1) if wsp else None,
                    },
                ))
            for m in _LOG_RE.finditer(text):
                op = m.group(1)
                log_counts[op] = log_counts.get(op, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["projects"] = sorted(projects)
        info.meta["workspaces"] = sorted(workspaces)
        info.meta["log_counts"] = dict(sorted(log_counts.items(),
                                               key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## COMET"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        projects = info.meta.get("projects") or []
        workspaces = info.meta.get("workspaces") or []
        if projects or workspaces:
            bits = []
            if projects:
                bits.append(f"projects: {', '.join(projects[:3])}")
            if workspaces:
                bits.append(f"workspaces: {', '.join(workspaces[:3])}")
            lines.append("- " + " · ".join(bits))
        log_counts = info.meta.get("log_counts") or {}
        if log_counts:
            shown = ", ".join(f"{k}×{v}" for k, v in list(log_counts.items())[:5])
            lines.append(f"- logs: {shown}")
        return truncate("\n".join(lines), budget_tokens)
