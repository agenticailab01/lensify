"""Pinecone adapter — surfaces clients, indexes, create_index configs, ops.

Triggers on `pinecone` imports. Supports both v3 (`Pinecone()` client) and
v2 legacy (`pinecone.init()` + `pinecone.Index("name")`).

Extracts:
    - Pinecone(api_key=...) / pinecone.init(...) client construction
    - pc.Index("name") / pinecone.Index("name") — captures index names
    - pc.create_index(name=..., dimension=..., metric=...) — captures
      index name + dimension + metric
    - .upsert(...) / .query(...) / .delete(...) op counts

Output: ## PINECONE capsule section.
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


# v3 client constructor
_CLIENT_V3_RE = re.compile(r"""(\w+)\s*=\s*Pinecone\s*\(""")
# v2 init
_INIT_V2_RE = re.compile(r"""\bpinecone\s*\.\s*init\s*\(""")
# Index access: pc.Index("name") or pinecone.Index("name")
_INDEX_RE = re.compile(
    r"""(?:(\w+)\s*=\s*)?\b(?:\w+|pinecone)\s*\.\s*Index\s*\(\s*['"]([^'"]+)['"]"""
)
# create_index — capture the full call (args up to closing paren) so we can
# run secondary regexes for dimension/metric on the body. Combining all in
# one regex breaks because optional + non-greedy groups collapse to zero-width.
_CREATE_RE = re.compile(r"""\bcreate_index\s*\(([^)]*)\)""", re.S)
_KW_NAME_RE = re.compile(r"""(?:^|\s|,)\s*(?:name\s*=\s*)?['"]([^'"]+)['"]""")
_KW_DIM_RE = re.compile(r"""dimension\s*=\s*(\d+)""")
_KW_METRIC_RE = re.compile(r"""metric\s*=\s*['"]([^'"]+)['"]""")
_UPSERT_RE = re.compile(r"""\.\s*upsert\s*\(""")
_QUERY_RE = re.compile(r"""\.\s*query\s*\(""")


class PineconeAdapter(FrameworkAdapter):
    name = "pinecone"
    detect_signatures = ("import pinecone", "from pinecone")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["pinecone"]

        entries: list[FrameworkEntry] = []
        indexes_referenced: set[str] = set()
        upsert_count = 0
        query_count = 0

        for rel_path, text in iter_python_with(parsed_files, walk_result, "pinecone"):
            for m in _CLIENT_V3_RE.finditer(text):
                entries.append(_entry("client", m.group(1), "Pinecone (v3)",
                                      rel_path, line_of(text, m.start())))
            for m in _INIT_V2_RE.finditer(text):
                entries.append(_entry("client", "pinecone", "init (v2)",
                                      rel_path, line_of(text, m.start())))
            for m in _INDEX_RE.finditer(text):
                var = m.group(1) or "(anon)"
                index_name = m.group(2)
                indexes_referenced.add(index_name)
                entries.append(_entry("index", var, f"Index({index_name!r})",
                                      rel_path, line_of(text, m.start()),
                                      index_name=index_name))
            for m in _CREATE_RE.finditer(text):
                body = m.group(1) or ""
                name_m = _KW_NAME_RE.search(body)
                if not name_m:
                    continue
                name = name_m.group(1)
                dim_m = _KW_DIM_RE.search(body)
                metric_m = _KW_METRIC_RE.search(body)
                dim = dim_m.group(1) if dim_m else None
                metric = metric_m.group(1) if metric_m else None
                sig = f"create_index({name!r}"
                if dim:
                    sig += f", dim={dim}"
                if metric:
                    sig += f", metric={metric!r}"
                sig += ")"
                entries.append(_entry("create", name, sig,
                                      rel_path, line_of(text, m.start()),
                                      dimension=dim, metric=metric))
                indexes_referenced.add(name)
            upsert_count += len(_UPSERT_RE.findall(text))
            query_count += len(_QUERY_RE.findall(text))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["indexes"] = sorted(indexes_referenced)
        info.meta["ops"] = {"upsert": upsert_count, "query": query_count}
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## PINECONE"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        idxs = info.meta.get("indexes") or []
        if idxs:
            lines.append(f"- indexes referenced: {', '.join(idxs[:6])}")
        ops = info.meta.get("ops") or {}
        if any(ops.values()):
            shown = ", ".join(f"{k}×{v}" for k, v in ops.items() if v)
            lines.append(f"- ops: {shown}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, sig: str, rel_path: str, line: int,
           **meta) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=sig,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": sig, **meta},
    )
