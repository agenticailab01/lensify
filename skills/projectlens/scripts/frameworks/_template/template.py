"""Reference adapter — copy and adapt for a new framework.

This file is the canonical example of how to write a ProjectLens framework
adapter. Read it top to bottom before copying. Every section is annotated
with WHY, not just WHAT.

Contract reminder (also in `references/adapter-sdk.md`):

    1. Adapter class MUST subclass FrameworkAdapter and set 4 class attrs:
         - name              # unique adapter id (manifest key)
         - detect_signatures # tuple of import strings / file fragments
         - priority          # 0-100, higher = higher capsule priority
         - max_entries       # capped at ABSOLUTE_MAX_ENTRIES (50)

    2. detect() MUST be O(1) — never open files. The default impl checks
       parsed_files imports; override only if your framework triggers on
       file presence (extension, basename) like Jupyter / Vue / Tailwind.

    3. extract() may open files but only those it cares about. Use
       `iter_python_with(parsed_files, walk_result, marker)` to filter to
       files importing `marker` BEFORE reading from disk.

    4. capsule_section() must respect budget_tokens. Use
       `truncate(text, budget)` to enforce.

    5. Adapter file MUST stay framework-free at hook-script level — the
       perf harness asserts hooks never import frameworks/ (Rule R1).

The example below extracts a make-believe framework's `Service(name=...)`
constructors. Replace the regex + naming and you have a real adapter.
"""
from __future__ import annotations

import re

# These dual-import lines support both package-import (production) and
# script-style import (when the perf harness runs adapters directly).
# Don't simplify — both forms have been needed in real bug reports.
try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


# ---- Regex patterns (one per kind of thing you want to surface) ----
# Tips:
#   • Anchor with `\b` where you can — prevents false positives
#   • Capture the variable name in group 1, the "class/op" in group 2
#   • Prefer non-overlapping patterns over one mega-regex
#   • If you need multi-line parsing, capture the args block then run
#     secondary regexes — combining `[^)]*?` + optional groups silently
#     collapses to zero-width matches (real bug found in this project).
_SERVICE_RE = re.compile(
    r"""(\w+)\s*=\s*Service\s*\(\s*(?:name\s*=\s*)?['"]([^'"]+)['"]"""
)


class TemplateAdapter(FrameworkAdapter):
    """Replace docstring + class name. Keep the structure."""

    # Required class attributes — see contract above.
    name = "template"
    detect_signatures = ("import myframework", "from myframework")
    priority = PRIORITY_MEDIUM
    max_entries = 20

    # ---- Optional: override detect() for non-import-based triggers ----
    # Example: trigger on file extension (like Jupyter):
    #
    # @classmethod
    # def detect(cls, walk_result, parsed_files) -> bool:
    #     for rec in walk_result.files:
    #         if getattr(rec, "language", None) == "MyLang":
    #             return True
    #     return False
    #
    # The default detect() implementation reads parsed_files' imports —
    # fine for 90% of frameworks.

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        """Walk parsed files and pull out structural records.

        Performance discipline:
          • Use iter_python_with(...) to filter to files actually importing
            your framework. Don't re-scan files that won't match.
          • Read file content once per file, run all regexes on the text.
          • Stop scanning at max_entries — caller enforces too, but bailing
            early saves work.
        """
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["myframework"]

        entries: list[FrameworkEntry] = []
        for rel_path, text in iter_python_with(
            parsed_files, walk_result, "myframework",
        ):
            for m in _SERVICE_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="service",
                    name=m.group(1),
                    signature=f"Service({m.group(2)!r})",
                    path=rel_path,
                    line=line_of(text, m.start()),
                    confidence="EXTRACTED",  # use INFERRED for fuzzy matches
                    meta={"service_name": m.group(2)},
                ))

        # Deterministic ordering — capsule output must be stable across runs.
        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        """Render the capsule section. Return None to opt out.

        Output format — keep it lean:
          • Section header `## NAME` (uppercase, descriptive)
          • One bullet per entry: `- kind \\`name\\` — signature (path:line)`
          • Trailing summary bullets if you have meta to show

        The budget is enforced via truncate() — anything over budget gets
        cut off at the nearest newline boundary.
        """
        if not info.entries:
            return None
        lines = ["## TEMPLATE"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        return truncate("\n".join(lines), budget_tokens)
