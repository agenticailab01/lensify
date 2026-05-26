"""Pydantic AI adapter — surfaces Agents, their tools and system prompts.

Triggers on `pydantic_ai` imports. Extracts:

    - Agent constructors (with optional generic typing: `Agent[Deps, Out]`)
    - @<agent>.tool / @<agent>.tool_plain decorators
    - @<agent>.system_prompt decorators
    - @<agent>.result_validator decorators

Output: ## PYDANTIC-AI capsule section, one entry per agent with tool count
and which lifecycle hooks are present.
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


_AGENT_RE = re.compile(
    r"""(\w+)\s*=\s*Agent\s*(?:\[[^\]]+\])?\s*\(\s*(['"]([^'"]+)['"])?"""
)
_TOOL_RE = re.compile(
    r"""@\s*(\w+)\s*\.\s*(tool|tool_plain)\b[^\n]*\n+\s*(?:async\s+)?def\s+(\w+)"""
)
_SYSPROMPT_RE = re.compile(r"""@\s*(\w+)\s*\.\s*system_prompt\b""")
_VALIDATOR_RE = re.compile(r"""@\s*(\w+)\s*\.\s*result_validator\b""")


class PydanticAIAdapter(FrameworkAdapter):
    name = "pydantic_ai"
    detect_signatures = ("import pydantic_ai", "from pydantic_ai")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["pydantic_ai"]

        # Two-pass: first find agents, then count decorators attributed by var name.
        agents: dict[str, dict] = {}  # name → {path, line, model, tools, has_sysprompt, has_validator}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "pydantic_ai"):
            for m in _AGENT_RE.finditer(text):
                var = m.group(1)
                model = m.group(3) or ""
                key = f"{rel_path}::{var}"
                agents[key] = {
                    "var": var, "path": rel_path, "line": line_of(text, m.start()),
                    "model": model, "tools": [],
                    "has_sysprompt": False, "has_validator": False,
                }
            for m in _TOOL_RE.finditer(text):
                var, _kind, fn = m.group(1), m.group(2), m.group(3)
                key = f"{rel_path}::{var}"
                if key in agents:
                    agents[key]["tools"].append(fn)
            for m in _SYSPROMPT_RE.finditer(text):
                key = f"{rel_path}::{m.group(1)}"
                if key in agents:
                    agents[key]["has_sysprompt"] = True
            for m in _VALIDATOR_RE.finditer(text):
                key = f"{rel_path}::{m.group(1)}"
                if key in agents:
                    agents[key]["has_validator"] = True

        entries: list[FrameworkEntry] = []
        for a in agents.values():
            entries.append(FrameworkEntry(
                kind="agent",
                name=a["var"],
                signature="Agent",
                path=a["path"], line=a["line"],
                confidence="EXTRACTED",
                meta={
                    "model": a["model"],
                    "tools": a["tools"],
                    "has_sysprompt": a["has_sysprompt"],
                    "has_validator": a["has_validator"],
                },
            ))
        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## PYDANTIC-AI"]
        for e in info.entries:
            m = e.meta
            model = m.get("model") or "?"
            lines.append(f"- agent `{e.name}` — model={model}  ({e.path}:{e.line})")
            tools = m.get("tools") or []
            if tools:
                lines.append(f"  - tools: {', '.join(tools[:8])}")
            flags = []
            if m.get("has_sysprompt"):
                flags.append("system_prompt")
            if m.get("has_validator"):
                flags.append("result_validator")
            if flags:
                lines.append(f"  - hooks: {', '.join(flags)}")
        return truncate("\n".join(lines), budget_tokens)
