"""Weights & Biases adapter — surfaces runs, logs, artifacts, sweeps.

Triggers on `wandb` imports. Extracts:

    - wandb.init(project=..., entity=..., name=..., config=...) — captures
      project + entity so the capsule shows where runs are landing
    - wandb.log(...) / wandb.log_artifact(...) call counts
    - wandb.Artifact(name=..., type=...) constructions
    - wandb.sweep(sweep_config) / wandb.agent(...) — sweep config
    - wandb.watch(model, ...) — model-watching calls

Output: ## WANDB capsule section.
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


_INIT_RE = re.compile(r"""\bwandb\s*\.\s*init\s*\(([^)]*)\)""", re.S)
_INIT_PROJECT_RE = re.compile(r"""project\s*=\s*['"]([^'"]+)['"]""")
_INIT_ENTITY_RE = re.compile(r"""entity\s*=\s*['"]([^'"]+)['"]""")
_INIT_NAME_RE = re.compile(r"""name\s*=\s*['"]([^'"]+)['"]""")

# Two-step: capture args block, then pull name + type separately. Single
# regex with optional + non-greedy collapses on the type kwarg.
_ARTIFACT_RE = re.compile(r"""wandb\s*\.\s*Artifact\s*\(([^)]*)\)""", re.S)
_ARTIFACT_NAME_RE = re.compile(r"""(?:^|\s|,)\s*(?:name\s*=\s*)?['"]([^'"]+)['"]""")
_ARTIFACT_TYPE_RE = re.compile(r"""type\s*=\s*['"]([^'"]+)['"]""")
_LOG_RE = re.compile(r"""\bwandb\s*\.\s*log\s*\(""")
_LOG_ARTIFACT_RE = re.compile(r"""\bwandb\s*\.\s*log_artifact\s*\(""")
_SWEEP_RE = re.compile(r"""\bwandb\s*\.\s*sweep\s*\(""")
_AGENT_RE = re.compile(r"""\bwandb\s*\.\s*agent\s*\(""")
_WATCH_RE = re.compile(r"""\bwandb\s*\.\s*watch\s*\(""")


class WandbAdapter(FrameworkAdapter):
    name = "wandb"
    detect_signatures = ("import wandb", "from wandb")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["wandb"]

        entries: list[FrameworkEntry] = []
        projects: set[str] = set()
        entities: set[str] = set()
        log_count = 0
        log_artifact_count = 0
        sweep_count = 0
        watch_count = 0

        for rel_path, text in iter_python_with(parsed_files, walk_result, "wandb"):
            for m in _INIT_RE.finditer(text):
                body = m.group(1) or ""
                proj = _INIT_PROJECT_RE.search(body)
                ent = _INIT_ENTITY_RE.search(body)
                name = _INIT_NAME_RE.search(body)
                if proj:
                    projects.add(proj.group(1))
                if ent:
                    entities.add(ent.group(1))
                sig = "wandb.init("
                bits = []
                if proj:
                    bits.append(f"project={proj.group(1)!r}")
                if ent:
                    bits.append(f"entity={ent.group(1)!r}")
                if name:
                    bits.append(f"name={name.group(1)!r}")
                sig += ", ".join(bits) + ")"
                entries.append(_entry("run", name.group(1) if name else "init",
                                      sig, rel_path, line_of(text, m.start()),
                                      project=proj.group(1) if proj else None,
                                      entity=ent.group(1) if ent else None))
            for m in _ARTIFACT_RE.finditer(text):
                body = m.group(1) or ""
                name_m = _ARTIFACT_NAME_RE.search(body)
                type_m = _ARTIFACT_TYPE_RE.search(body)
                if not name_m:
                    continue
                aname = name_m.group(1)
                atype = type_m.group(1) if type_m else "?"
                entries.append(_entry("artifact", aname,
                                      f"Artifact({aname!r}, type={atype!r})",
                                      rel_path, line_of(text, m.start()),
                                      artifact_type=atype))
            log_count += len(_LOG_RE.findall(text))
            log_artifact_count += len(_LOG_ARTIFACT_RE.findall(text))
            sweep_count += len(_SWEEP_RE.findall(text))
            sweep_count += len(_AGENT_RE.findall(text))
            watch_count += len(_WATCH_RE.findall(text))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["projects"] = sorted(projects)
        info.meta["entities"] = sorted(entities)
        info.meta["ops"] = {
            "log": log_count, "log_artifact": log_artifact_count,
            "sweep_or_agent": sweep_count, "watch": watch_count,
        }
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("ops", {}).get("log"):
            return None
        lines = ["## WANDB"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        projects = info.meta.get("projects") or []
        if projects:
            lines.append(f"- projects: {', '.join(projects[:4])}")
        ops = info.meta.get("ops") or {}
        nonzero = {k: v for k, v in ops.items() if v}
        if nonzero:
            shown = ", ".join(f"{k}×{v}" for k, v in nonzero.items())
            lines.append(f"- ops: {shown}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, sig: str, rel_path: str, line: int,
           **meta) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=sig,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": sig, **meta},
    )
