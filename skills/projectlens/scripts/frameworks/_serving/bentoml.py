"""BentoML adapter — surfaces services, APIs, runners.

Triggers on `bentoml` imports. Extracts:

    - @bentoml.service-decorated classes (the deployable units)
    - @bentoml.api / @bentoml.task / @bentoml.async_task endpoints
    - bentoml.Runner(...) and bentoml.runner constructions
    - bentoml.io.* schemas (NumpyNdarray, JSON, Image, Text, …)

Output: ## BENTOML capsule section.
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


_SERVICE_RE = re.compile(
    r"""@\s*bentoml\s*\.\s*service\b[^\n]*\n+\s*class\s+(\w+)"""
)
_API_RE = re.compile(
    r"""@\s*bentoml\s*\.\s*(api|task|async_task)\b[^\n]*\n+\s*(?:async\s+)?def\s+(\w+)"""
)
_RUNNER_RE = re.compile(
    r"""(\w+)\s*=\s*bentoml\s*\.\s*Runner\s*\("""
)
# Match both `bentoml.io.NumpyNdarray(...)` and bare `NumpyNdarray(...)`
# (the latter when imported via `from bentoml.io import NumpyNdarray`).
# Use word boundary to avoid catching `MyNumpyNdarray`.
_IO_RE = re.compile(
    r"""(?:bentoml\s*\.\s*io\s*\.\s*)?\b(NumpyNdarray|PandasDataFrame|"""
    r"""PandasSeries|Multipart)\s*\("""
)
# Match only when context indicates these names came from bentoml.io.
# Names like `Image`, `Text`, `JSON`, `File` are too generic to match bare.
_IO_QUALIFIED_RE = re.compile(
    r"""bentoml\s*\.\s*io\s*\.\s*(JSON|Image|Text|File)\s*\("""
)


class BentoMLAdapter(FrameworkAdapter):
    name = "bentoml"
    detect_signatures = ("import bentoml", "from bentoml")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["bentoml"]

        entries: list[FrameworkEntry] = []
        io_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "bentoml"):
            for m in _SERVICE_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="service",
                    name=m.group(1),
                    signature="@bentoml.service",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(1)},
                ))
            for m in _API_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="endpoint",
                    name=m.group(2),
                    signature=f"@bentoml.{m.group(1)}",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"kind": m.group(1)},
                ))
            for m in _RUNNER_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="runner",
                    name=m.group(1),
                    signature="Runner",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": "Runner"},
                ))
            for m in _IO_RE.finditer(text):
                io = m.group(1)
                io_counts[io] = io_counts.get(io, 0) + 1
            for m in _IO_QUALIFIED_RE.finditer(text):
                io = m.group(1)
                io_counts[io] = io_counts.get(io, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["io_types"] = dict(sorted(io_counts.items(),
                                             key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## BENTOML"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        io = info.meta.get("io_types") or {}
        if io:
            top = ", ".join(f"{k}×{v}" for k, v in list(io.items())[:5])
            lines.append(f"- I/O schemas: {top}")
        return truncate("\n".join(lines), budget_tokens)
