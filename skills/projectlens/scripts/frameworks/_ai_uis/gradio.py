"""Gradio adapter — surfaces interfaces, blocks, components, launch entries.

Triggers on `gradio` imports. Extracts:

    - gr.Interface(fn=..., inputs=..., outputs=..., title="…")
    - gr.Blocks(title="…") + nested components
    - gr.ChatInterface(fn=..., title="…")
    - Component constructions: gr.Textbox, gr.Image, gr.Slider, gr.Audio,
      gr.Video, gr.File, gr.Dataframe, gr.Number, gr.Markdown, gr.Button,
      gr.Dropdown, gr.Radio, gr.Checkbox, gr.Code
    - .launch(...) calls (entry points)

Output: ## GRADIO capsule section.
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


_INTERFACE_RE = re.compile(
    r"""(\w+)\s*=\s*gr\s*\.\s*(Interface|ChatInterface|TabbedInterface)\s*\("""
)
_BLOCKS_RE = re.compile(r"""(?:(\w+)\s*=\s*)?gr\s*\.\s*Blocks\s*\(""")
_COMPONENT_RE = re.compile(
    r"""\bgr\s*\.\s*(Textbox|Image|Slider|Audio|Video|File|Dataframe|"""
    r"""Number|Markdown|Button|Dropdown|Radio|Checkbox|CheckboxGroup|"""
    r"""Code|HTML|JSON|Label|Gallery|Plot|Model3D|HighlightedText|"""
    r"""ColorPicker|DateTime|AnnotatedImage|Chatbot)\s*\("""
)
_LAUNCH_RE = re.compile(r"""(\w+)\s*\.\s*launch\s*\(""")
_TITLE_RE = re.compile(r"""title\s*=\s*['"]([^'"]+)['"]""")


class GradioAdapter(FrameworkAdapter):
    name = "gradio"
    detect_signatures = ("import gradio", "from gradio")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["gradio"]

        entries: list[FrameworkEntry] = []
        launches: list[tuple[str, str, int]] = []  # (var, path, line)
        component_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "gradio"):
            for m in _INTERFACE_RE.finditer(text):
                # Look ahead for a title kwarg in the same call (best-effort)
                tail = text[m.start(): m.start() + 400]
                title_m = _TITLE_RE.search(tail)
                entries.append(FrameworkEntry(
                    kind="interface",
                    name=m.group(1),
                    signature=m.group(2),
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(2), "title": title_m.group(1) if title_m else ""},
                ))
            for m in _BLOCKS_RE.finditer(text):
                name = m.group(1) or "anonymous"
                tail = text[m.start(): m.start() + 400]
                title_m = _TITLE_RE.search(tail)
                entries.append(FrameworkEntry(
                    kind="blocks",
                    name=name,
                    signature="Blocks",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": "Blocks", "title": title_m.group(1) if title_m else ""},
                ))
            for m in _COMPONENT_RE.finditer(text):
                comp = m.group(1)
                component_counts[comp] = component_counts.get(comp, 0) + 1
            for m in _LAUNCH_RE.finditer(text):
                launches.append((m.group(1), rel_path, line_of(text, m.start())))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["components"] = dict(sorted(component_counts.items(),
                                              key=lambda kv: -kv[1]))
        info.meta["launches"] = launches
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("launches"):
            return None
        lines = ["## GRADIO"]
        for e in info.entries:
            title = e.meta.get("title")
            title_str = f" — {title!r}" if title else ""
            lines.append(f"- {e.kind} `{e.name}` ({e.meta.get('class')}){title_str}  ({e.path}:{e.line})")
        comps = info.meta.get("components") or {}
        if comps:
            top = ", ".join(f"{k}×{v}" for k, v in list(comps.items())[:6])
            lines.append(f"- components: {top}")
        launches = info.meta.get("launches") or []
        if launches:
            entrypoints = sorted({f"{path}:{ln}" for _, path, ln in launches})
            lines.append(f"- .launch() at: {', '.join(entrypoints[:3])}")
        return truncate("\n".join(lines), budget_tokens)
