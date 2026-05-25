"""Chainlit adapter — surfaces lifecycle handlers and message UI primitives.

Triggers on `chainlit` imports. Extracts:

    - Lifecycle decorators: @cl.on_message, @cl.on_chat_start,
      @cl.on_chat_end, @cl.on_audio_chunk, @cl.on_settings_update,
      @cl.on_chat_resume, @cl.action_callback, @cl.step, @cl.password_auth_callback
    - UI primitives: cl.Message(...), cl.Step(...), cl.Action(...),
      cl.AskUserMessage(...), cl.File(...), cl.Image(...)

Output: ## CHAINLIT capsule section.
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


_HANDLER_RE = re.compile(
    r"""@\s*cl\s*\.\s*(on_message|on_chat_start|on_chat_end|on_chat_resume|"""
    r"""on_audio_chunk|on_settings_update|on_logout|on_stop|step|"""
    r"""action_callback|password_auth_callback|header_auth_callback|"""
    r"""oauth_callback|set_chat_profiles|author_rename)\b[^\n]*\n+\s*(?:async\s+)?def\s+(\w+)"""
)
_UI_RE = re.compile(
    r"""\bcl\s*\.\s*(Message|Step|Action|AskUserMessage|AskActionMessage|"""
    r"""AskFileMessage|File|Image|Audio|Video|Plotly|Pdf|Text|TaskList|"""
    r"""Task|ChatSettings|ChatProfile|Avatar)\s*\("""
)


class ChainlitAdapter(FrameworkAdapter):
    name = "chainlit"
    detect_signatures = ("import chainlit", "from chainlit")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["chainlit"]

        entries: list[FrameworkEntry] = []
        ui_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "chainlit"):
            for m in _HANDLER_RE.finditer(text):
                event = m.group(1)
                fn = m.group(2)
                entries.append(FrameworkEntry(
                    kind="handler",
                    name=fn,
                    signature=f"@cl.{event}",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"event": event},
                ))
            for m in _UI_RE.finditer(text):
                kind_name = m.group(1)
                ui_counts[kind_name] = ui_counts.get(kind_name, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["ui_primitives"] = dict(sorted(ui_counts.items(),
                                                  key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("ui_primitives"):
            return None
        lines = ["## CHAINLIT"]
        for e in info.entries:
            lines.append(f"- handler `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        ui = info.meta.get("ui_primitives") or {}
        if ui:
            top = ", ".join(f"{k}×{v}" for k, v in list(ui.items())[:5])
            lines.append(f"- UI primitives: {top}")
        return truncate("\n".join(lines), budget_tokens)
