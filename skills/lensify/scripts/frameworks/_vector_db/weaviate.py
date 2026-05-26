"""Weaviate adapter — surfaces clients, collections, and query primitives.

Triggers on `weaviate` imports. Supports both v3 legacy (`weaviate.Client`)
and v4 (`connect_to_local`/`connect_to_wcs`/`WeaviateClient`).

Extracts:
    - Client constructors: weaviate.Client(...), WeaviateClient(...),
      connect_to_local/connect_to_wcs/connect_to_embedded()
    - client.collections.create(name="X", ...) — collection creates
    - client.collections.get("X") — collection access
    - Query primitives: .near_vector / .near_text / .hybrid / .bm25 /
      .fetch_objects / .aggregate

Output: ## WEAVIATE capsule section.
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


_CLIENT_RE = re.compile(
    r"""(\w+)\s*=\s*(?:weaviate\s*\.\s*)?"""
    r"""(Client|WeaviateClient|connect_to_local|connect_to_wcs|connect_to_embedded|connect_to_custom)\s*\("""
)
_COLLECTION_CREATE_RE = re.compile(
    r"""\.\s*collections\s*\.\s*create\s*\(\s*(?:name\s*=\s*)?['"]([^'"]+)['"]"""
)
_COLLECTION_GET_RE = re.compile(
    r"""\.\s*collections\s*\.\s*get\s*\(\s*['"]([^'"]+)['"]"""
)
_QUERY_RE = re.compile(
    r"""\.\s*(near_vector|near_text|hybrid|bm25|fetch_objects|aggregate)\s*\("""
)


class WeaviateAdapter(FrameworkAdapter):
    name = "weaviate"
    detect_signatures = ("import weaviate", "from weaviate")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["weaviate"]

        entries: list[FrameworkEntry] = []
        collections: set[str] = set()
        query_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "weaviate"):
            for m in _CLIENT_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="client",
                    name=m.group(1),
                    signature=m.group(2),
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(2)},
                ))
            for m in _COLLECTION_CREATE_RE.finditer(text):
                col = m.group(1)
                collections.add(col)
                entries.append(FrameworkEntry(
                    kind="collection",
                    name=col,
                    signature=f"collections.create({col!r})",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"op": "create", "name": col},
                ))
            for m in _COLLECTION_GET_RE.finditer(text):
                collections.add(m.group(1))
            for m in _QUERY_RE.finditer(text):
                q = m.group(1)
                query_counts[q] = query_counts.get(q, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["collections_referenced"] = sorted(collections)
        info.meta["query_counts"] = dict(sorted(query_counts.items(),
                                                 key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("collections_referenced"):
            return None
        lines = ["## WEAVIATE"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        cols = info.meta.get("collections_referenced") or []
        if cols:
            lines.append(f"- collections: {', '.join(cols[:8])}")
        qc = info.meta.get("query_counts") or {}
        if qc:
            shown = ", ".join(f"{k}×{v}" for k, v in list(qc.items())[:5])
            lines.append(f"- queries: {shown}")
        return truncate("\n".join(lines), budget_tokens)
