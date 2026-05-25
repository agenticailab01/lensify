"""Chroma adapter — surfaces clients, collections, embedding ops.

Triggers on `chromadb` imports. Extracts:

    - chromadb.Client() / PersistentClient(path=...) / HttpClient(host=...,port=...)
      / EphemeralClient() / CloudClient(...) constructions
    - client.create_collection(name=..., embedding_function=...)
    - client.get_or_create_collection(name=...)
    - client.get_collection(name=...)
    - .add(...), .query(...), .update(...), .upsert(...), .delete(...) op counts

Output: ## CHROMA capsule section.
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
    r"""(\w+)\s*=\s*chromadb\s*\.\s*(Client|PersistentClient|HttpClient|EphemeralClient|CloudClient)\s*\("""
)
_COLLECTION_RE = re.compile(
    r"""(\w+)\s*=\s*\w+\s*\.\s*(create_collection|get_or_create_collection|get_collection)\s*\(\s*(?:name\s*=\s*)?['"]([^'"]+)['"]"""
)
_OP_RE = re.compile(
    r"""\.\s*(add|query|update|upsert|delete|peek)\s*\("""
)
_EMBED_FN_RE = re.compile(
    r"""embedding_function\s*=\s*([\w.]+)"""
)


class ChromaAdapter(FrameworkAdapter):
    name = "chroma"
    detect_signatures = ("import chromadb", "from chromadb")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["chromadb"]

        entries: list[FrameworkEntry] = []
        collections: set[str] = set()
        embed_fns: set[str] = set()
        op_counts: dict[str, int] = {}

        for rel_path, text in iter_python_with(parsed_files, walk_result, "chromadb"):
            for m in _CLIENT_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="client",
                    name=m.group(1),
                    signature=m.group(2),
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(2)},
                ))
            for m in _COLLECTION_RE.finditer(text):
                var = m.group(1)
                op = m.group(2)
                col_name = m.group(3)
                collections.add(col_name)
                entries.append(FrameworkEntry(
                    kind="collection",
                    name=var,
                    signature=f"{op}({col_name!r})",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"op": op, "collection_name": col_name},
                ))
            for m in _EMBED_FN_RE.finditer(text):
                embed_fns.add(m.group(1))
            for m in _OP_RE.finditer(text):
                op = m.group(1)
                op_counts[op] = op_counts.get(op, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["collections"] = sorted(collections)
        info.meta["embedding_functions"] = sorted(embed_fns)
        info.meta["ops"] = dict(sorted(op_counts.items(), key=lambda kv: -kv[1]))
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## CHROMA"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        cols = info.meta.get("collections") or []
        if cols:
            lines.append(f"- collections: {', '.join(cols[:6])}")
        embeds = info.meta.get("embedding_functions") or []
        if embeds:
            lines.append(f"- embedding fns: {', '.join(embeds[:4])}")
        ops = info.meta.get("ops") or {}
        if ops:
            shown = ", ".join(f"{k}×{v}" for k, v in list(ops.items())[:5])
            lines.append(f"- ops: {shown}")
        return truncate("\n".join(lines), budget_tokens)
