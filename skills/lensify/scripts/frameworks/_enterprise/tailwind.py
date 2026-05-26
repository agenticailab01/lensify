"""Tailwind CSS adapter — surfaces config customisations.

Triggers on the presence of any `tailwind.config.{js,ts,cjs,mjs}` file in
the project (file-presence detection, like Jupyter / Vue).

Extracts from the config file:

    - `content:` array (file globs scanned for utilities) — first 5
    - `theme.extend.colors` keys (custom palette names)
    - `theme.extend.fontFamily` keys
    - `theme.extend.spacing` / `screens` / `borderRadius` extension presence
    - `plugins:` array — names of plugins like @tailwindcss/forms etc.

Output: ## TAILWIND capsule section summarising the design tokens that
diverge from defaults. Reading this gives an agent the "design contract"
without needing to read the whole config file.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from .._util import truncate, safe_read
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from _util import truncate, safe_read  # type: ignore[no-redef]


_TAILWIND_CONFIG_NAMES = (
    "tailwind.config.js",
    "tailwind.config.ts",
    "tailwind.config.cjs",
    "tailwind.config.mjs",
)

_CONTENT_RE = re.compile(r"""content\s*:\s*\[([^\]]*)\]""", re.S)
_THEME_EXTEND_RE = re.compile(r"""extend\s*:\s*\{(.*?)\n\s*\}""", re.S)
_COLORS_RE = re.compile(r"""colors\s*:\s*\{([^}]*)\}""", re.S)
_FONT_FAMILY_RE = re.compile(r"""fontFamily\s*:\s*\{([^}]*)\}""", re.S)
_SPACING_RE = re.compile(r"""\bspacing\s*:""")
_SCREENS_RE = re.compile(r"""\bscreens\s*:""")
_BORDER_RADIUS_RE = re.compile(r"""\bborderRadius\s*:""")
_PLUGINS_RE = re.compile(r"""plugins\s*:\s*\[([^\]]*)\]""", re.S)
_REQUIRE_RE = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")
_IMPORT_RE = re.compile(r"""import\s+\w+\s+from\s+['"]([^'"]+)['"]""")


class TailwindAdapter(FrameworkAdapter):
    name = "tailwind"
    detect_signatures = ("tailwind",)  # placeholder; real detection below
    priority = PRIORITY_MEDIUM
    max_entries = 5

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        """Detect on tailwind.config.* file presence."""
        for rec in walk_result.files:
            basename = Path(rec.path).name
            if basename in _TAILWIND_CONFIG_NAMES:
                return True
        return False

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["tailwind.config.*"]

        entries: list[FrameworkEntry] = []
        for rec in walk_result.files:
            basename = Path(rec.path).name
            if basename not in _TAILWIND_CONFIG_NAMES:
                continue
            text = safe_read(rec.abs_path)
            if text is None:
                continue

            content_globs: list[str] = []
            content_m = _CONTENT_RE.search(text)
            if content_m:
                content_globs = re.findall(
                    r"""['"]([^'"]+)['"]""", content_m.group(1)
                )

            colors: list[str] = []
            fonts: list[str] = []
            has_spacing = False
            has_screens = False
            has_radius = False
            extend_m = _THEME_EXTEND_RE.search(text)
            if extend_m:
                body = extend_m.group(1)
                col_m = _COLORS_RE.search(body)
                if col_m:
                    colors = re.findall(r"""(\w+)\s*:""", col_m.group(1))[:12]
                ff_m = _FONT_FAMILY_RE.search(body)
                if ff_m:
                    fonts = re.findall(r"""(\w+)\s*:""", ff_m.group(1))[:6]
                has_spacing = bool(_SPACING_RE.search(body))
                has_screens = bool(_SCREENS_RE.search(body))
                has_radius = bool(_BORDER_RADIUS_RE.search(body))

            plugins: list[str] = []
            plugins_m = _PLUGINS_RE.search(text)
            if plugins_m:
                pb = plugins_m.group(1)
                # require("@tailwindcss/forms") or imports above
                plugins = _REQUIRE_RE.findall(pb)
            if not plugins:
                # Fall back to top-of-file imports/requires
                plugins = (_REQUIRE_RE.findall(text)[:6]
                           + _IMPORT_RE.findall(text)[:6])

            entries.append(FrameworkEntry(
                kind="config",
                name=basename,
                signature="tailwind config",
                path=rec.path, line=1,
                confidence="EXTRACTED",
                meta={
                    "content": content_globs[:5],
                    "custom_colors": colors,
                    "custom_fonts": fonts,
                    "has_spacing_extension": has_spacing,
                    "has_screens_extension": has_screens,
                    "has_borderRadius_extension": has_radius,
                    "plugins": plugins,
                },
            ))

        info.entries = cap_entries(entries, self.max_entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## TAILWIND"]
        for e in info.entries:
            m = e.meta
            lines.append(f"- config `{e.name}`  ({e.path})")
            if m.get("custom_colors"):
                lines.append(f"  - custom colors: {', '.join(m['custom_colors'][:6])}")
            if m.get("custom_fonts"):
                lines.append(f"  - custom fonts: {', '.join(m['custom_fonts'][:4])}")
            ext_flags = []
            if m.get("has_spacing_extension"):
                ext_flags.append("spacing")
            if m.get("has_screens_extension"):
                ext_flags.append("screens")
            if m.get("has_borderRadius_extension"):
                ext_flags.append("borderRadius")
            if ext_flags:
                lines.append(f"  - extends: {', '.join(ext_flags)}")
            if m.get("plugins"):
                lines.append(f"  - plugins: {', '.join(m['plugins'][:4])}")
            if m.get("content"):
                lines.append(f"  - content: {', '.join(m['content'][:3])}")
        return truncate("\n".join(lines), budget_tokens)
