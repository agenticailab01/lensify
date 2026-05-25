"""Streamlit adapter — surfaces pages, widgets, forms, cached functions.

Triggers on `streamlit` imports. Extracts:

    - Pages: files containing `st.set_page_config(...)` plus files in
      ``pages/`` subdirectory (Streamlit's auto-multipage convention)
    - Widget counts per page: st.button, st.slider, st.text_input,
      st.chat_input, st.chat_message, st.selectbox, st.file_uploader,
      st.dataframe, st.write, st.markdown, st.metric
    - Forms: `st.form(...)` blocks
    - @st.cache_data / @st.cache_resource decorated functions
    - Whether `st.session_state` is used

Output: ## STREAMLIT capsule section, one entry per page with widget mix.
"""
from __future__ import annotations

import re
from pathlib import Path

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


_PAGE_CONFIG_RE = re.compile(r"""st\s*\.\s*set_page_config\s*\(""")
_WIDGET_RE = re.compile(
    r"""\bst\s*\.\s*(button|slider|text_input|text_area|chat_input|"""
    r"""chat_message|selectbox|multiselect|radio|checkbox|file_uploader|"""
    r"""date_input|time_input|color_picker|number_input|dataframe|write|"""
    r"""markdown|metric|table|image|video|audio|map|plotly_chart|"""
    r"""altair_chart|line_chart|bar_chart|area_chart|pyplot|tabs|expander|"""
    r"""columns|container|sidebar|status|toast|spinner|progress)\s*\("""
)
_FORM_RE = re.compile(r"""st\s*\.\s*form\s*\(\s*['"]?(\w+)?['"]?""")
_CACHE_RE = re.compile(
    r"""@\s*st\s*\.\s*(cache_data|cache_resource)\b[^\n]*\n+\s*(?:async\s+)?def\s+(\w+)"""
)
_SESSION_STATE_RE = re.compile(r"""st\s*\.\s*session_state\b""")


class StreamlitAdapter(FrameworkAdapter):
    name = "streamlit"
    detect_signatures = ("import streamlit", "from streamlit")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["streamlit"]

        entries: list[FrameworkEntry] = []
        cached_fns: list[tuple[str, str, str, int]] = []  # (fn, kind, path, line)
        uses_session_state: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "streamlit"):
            # Page detection: explicit set_page_config OR in pages/ dir OR root
            has_page_config = bool(_PAGE_CONFIG_RE.search(text))
            in_pages_dir = "/pages/" in f"/{rel_path}" or rel_path.startswith("pages/")
            is_root_app = Path(rel_path).name in ("app.py", "main.py", "Home.py", "streamlit_app.py")
            is_page = has_page_config or in_pages_dir or is_root_app

            widget_counts: dict[str, int] = {}
            for m in _WIDGET_RE.finditer(text):
                w = m.group(1)
                widget_counts[w] = widget_counts.get(w, 0) + 1
            forms = [m.group(1) or "(anonymous)" for m in _FORM_RE.finditer(text)]
            if _SESSION_STATE_RE.search(text):
                uses_session_state.add(rel_path)

            for m in _CACHE_RE.finditer(text):
                cached_fns.append((m.group(2), m.group(1), rel_path, line_of(text, m.start())))

            if is_page and (widget_counts or forms or has_page_config):
                line = 1
                if has_page_config:
                    pc_m = _PAGE_CONFIG_RE.search(text)
                    if pc_m:
                        line = line_of(text, pc_m.start())
                entries.append(FrameworkEntry(
                    kind="page",
                    name=Path(rel_path).stem,
                    signature="page",
                    path=rel_path, line=line,
                    confidence="EXTRACTED",
                    meta={
                        "widgets": dict(sorted(widget_counts.items(),
                                               key=lambda kv: -kv[1])),
                        "forms": forms,
                        "has_page_config": has_page_config,
                        "uses_session_state": rel_path in uses_session_state,
                    },
                ))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["cached_fns"] = cached_fns
        info.meta["session_state_files"] = sorted(uses_session_state)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("cached_fns"):
            return None
        lines = ["## STREAMLIT"]
        for e in info.entries:
            m = e.meta
            top_widgets = list(m.get("widgets", {}).items())[:5]
            widget_str = ", ".join(f"{k}×{v}" for k, v in top_widgets) if top_widgets else "(no widgets)"
            extra = []
            if m.get("forms"):
                extra.append(f"{len(m['forms'])} form(s)")
            if m.get("uses_session_state"):
                extra.append("session_state")
            extra_str = f"  ·  {' · '.join(extra)}" if extra else ""
            lines.append(f"- page `{e.name}` — {widget_str}{extra_str}  ({e.path}:{e.line})")
        cached = info.meta.get("cached_fns") or []
        if cached:
            shown = ", ".join(f"{fn} ({kind})" for fn, kind, _, _ in cached[:5])
            lines.append(f"- cached: {shown}")
        return truncate("\n".join(lines), budget_tokens)
