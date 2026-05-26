"""Qdrant adapter — surfaces clients, collections, vector configs, ops.

Triggers on `qdrant_client` imports. Extracts:

    - QdrantClient(url=..., host=..., path=...) constructions
    - .create_collection(collection_name="X", vectors_config=VectorParams(size=N, distance=D))
    - .upsert(collection_name="X", ...) / .search(...) / .delete(...) /
      .scroll(...) / .retrieve(...) op counts
    - .recreate_collection(...) calls (destructive)

Output: ## QDRANT capsule section.
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
    r"""(\w+)\s*=\s*(?:Async)?QdrantClient\s*\("""
)
# Two-step capture: first grab the create call + name, then scan a window
# of text following the call (next ~400 chars) for size/distance — the
# VectorParams call typically lives in the same paren group but may span
# multiple lines and use VectorParams(...) on a separate argument.
_CREATE_RE = re.compile(
    r"""\.\s*(create_collection|recreate_collection)\s*\(\s*(?:collection_name\s*=\s*)?['"]([^'"]+)['"]"""
)
_SIZE_RE = re.compile(r"""size\s*=\s*(\d+)""")
_DISTANCE_RE = re.compile(r"""distance\s*=\s*(?:Distance\.|distances\.)?(\w+)""")
_OP_RE = re.compile(
    r"""\.\s*(upsert|search|delete|scroll|retrieve|count)\s*\(\s*(?:collection_name\s*=\s*)?['"]?([\w-]+)?"""
)


class QdrantAdapter(FrameworkAdapter):
    name = "qdrant"
    detect_signatures = ("import qdrant_client", "from qdrant_client")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["qdrant_client"]

        entries: list[FrameworkEntry] = []
        collections: set[str] = set()
        op_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "qdrant_client"):
            for m in _CLIENT_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="client",
                    name=m.group(1),
                    signature="QdrantClient",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": "QdrantClient"},
                ))
            for m in _CREATE_RE.finditer(text):
                op = m.group(1)
                col = m.group(2)
                # Look in the next ~400 chars for size/distance kwargs (handles
                # multi-line create_collection(... vectors_config=VectorParams(size=...)) )
                window = text[m.start(): m.start() + 500]
                size_m = _SIZE_RE.search(window)
                distance_m = _DISTANCE_RE.search(window)
                size = size_m.group(1) if size_m else None
                distance = distance_m.group(1) if distance_m else None
                collections.add(col)
                sig = f"{op}({col!r}"
                if size:
                    sig += f", size={size}"
                if distance:
                    sig += f", distance={distance}"
                sig += ")"
                entries.append(FrameworkEntry(
                    kind="collection",
                    name=col,
                    signature=sig,
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"op": op, "size": size, "distance": distance, "name": col},
                ))
            for m in _OP_RE.finditer(text):
                op = m.group(1)
                col = m.group(2) or ""
                op_counts[op] = op_counts.get(op, 0) + 1
                if col and col != "collection_name":
                    collections.add(col)

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["collections"] = sorted(collections)
        info.meta["ops"] = dict(sorted(op_counts.items(), key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("collections"):
            return None
        lines = ["## QDRANT"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        cols = info.meta.get("collections") or []
        if cols:
            lines.append(f"- collections: {', '.join(cols[:6])}")
        ops = info.meta.get("ops") or {}
        if ops:
            shown = ", ".join(f"{k}×{v}" for k, v in list(ops.items())[:5])
            lines.append(f"- ops: {shown}")
        return truncate("\n".join(lines), budget_tokens)
