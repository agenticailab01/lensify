"""Vue Single-File Component adapter — surfaces components, props, emits, composables.

Triggers on the presence of any `.vue` file (walker recognises Vue as a
language). Per-file extraction parses the SFC structure:

    - <script setup> vs Options API detection
    - defineProps / props option
    - defineEmits / emits option
    - defineExpose
    - Composables used (anything called `useX(...)` imported)

Output: ## VUE capsule section listing components with their interface.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from .._util import truncate, line_of, safe_read
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from _util import truncate, line_of, safe_read  # type: ignore[no-redef]


_SCRIPT_SETUP_RE = re.compile(r"""<script\s+setup\b""")
_SCRIPT_RE = re.compile(r"""<script[^>]*>""")
_DEFINE_PROPS_RE = re.compile(r"""defineProps\s*<?([^>]*)>?\s*\(""")
_DEFINE_EMITS_RE = re.compile(r"""defineEmits\s*<?[^>]*>?\s*\(\s*\[([^\]]*)\]""")
_DEFINE_EXPOSE_RE = re.compile(r"""defineExpose\s*\(""")
# `useX(...)` imported and called
_COMPOSABLE_USE_RE = re.compile(r"""\b(use[A-Z]\w+)\s*\(""")
# Options API
_PROPS_OPTION_RE = re.compile(r"""\bprops\s*:\s*\{([^}]+)\}""", re.S)
_EMITS_OPTION_RE = re.compile(r"""\bemits\s*:\s*\[([^\]]*)\]""")


class VueAdapter(FrameworkAdapter):
    name = "vue"
    detect_signatures = ("vue",)  # placeholder, real detection below
    priority = PRIORITY_HIGH
    max_entries = 30

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        """Trigger on .vue file presence — O(1) over walker file records."""
        for rec in walk_result.files:
            if getattr(rec, "language", None) == "Vue":
                return True
        return False

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = [".vue"]

        entries: list[FrameworkEntry] = []
        composable_counts: dict[str, int] = {}

        vue_files = [r for r in walk_result.files
                     if getattr(r, "language", None) == "Vue"]
        for rec in vue_files:
            text = safe_read(rec.abs_path)
            if text is None:
                continue
            is_setup = bool(_SCRIPT_SETUP_RE.search(text))
            has_script = bool(_SCRIPT_RE.search(text))
            api_style = "setup" if is_setup else ("options" if has_script else "template-only")

            # Props
            props: list[str] = []
            for m in _DEFINE_PROPS_RE.finditer(text):
                # Try to pull names from the call: defineProps({foo: ..., bar: ...})
                tail = text[m.end(): m.end() + 600]
                # Look for object keys or array of strings
                arr_m = re.search(r"""\[([^\]]*)\]""", tail)
                if arr_m:
                    props.extend(re.findall(r"""['"]([^'"]+)['"]""", arr_m.group(1)))
                else:
                    obj_m = re.search(r"""\{([^}]*)\}""", tail)
                    if obj_m:
                        props.extend(re.findall(r"""(\w+)\s*:""", obj_m.group(1)))
            if not is_setup:
                for m in _PROPS_OPTION_RE.finditer(text):
                    props.extend(re.findall(r"""(\w+)\s*:""", m.group(1)))

            # Emits
            emits: list[str] = []
            for m in _DEFINE_EMITS_RE.finditer(text):
                emits.extend(re.findall(r"""['"]([^'"]+)['"]""", m.group(1)))
            for m in _EMITS_OPTION_RE.finditer(text):
                emits.extend(re.findall(r"""['"]([^'"]+)['"]""", m.group(1)))

            # Composables — `useX(...)` invocations
            local_composables: set[str] = set()
            for m in _COMPOSABLE_USE_RE.finditer(text):
                name = m.group(1)
                local_composables.add(name)
                composable_counts[name] = composable_counts.get(name, 0) + 1

            has_expose = bool(_DEFINE_EXPOSE_RE.search(text))

            entries.append(FrameworkEntry(
                kind="component",
                name=Path(rec.path).stem,
                signature=f"Vue SFC ({api_style})",
                path=rec.path, line=1,
                confidence="EXTRACTED",
                meta={
                    "api_style": api_style,
                    "props": props[:12],
                    "emits": emits[:8],
                    "composables": sorted(local_composables)[:8],
                    "exposes": has_expose,
                },
            ))

        entries.sort(key=lambda e: e.path)
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["composable_usage"] = dict(sorted(composable_counts.items(),
                                                     key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## VUE"]
        for e in info.entries:
            m = e.meta
            bits = [f"api={m.get('api_style', '?')}"]
            if m.get("props"):
                bits.append(f"props={len(m['props'])}")
            if m.get("emits"):
                bits.append(f"emits={len(m['emits'])}")
            lines.append(f"- component `{e.name}` — {', '.join(bits)}  ({e.path})")
            if m.get("emits"):
                lines.append(f"  - emits: {', '.join(m['emits'][:5])}")
        comp_usage = info.meta.get("composable_usage") or {}
        if comp_usage:
            top = ", ".join(f"{k}×{v}" for k, v in list(comp_usage.items())[:5])
            lines.append(f"- composables: {top}")
        return truncate("\n".join(lines), budget_tokens)
