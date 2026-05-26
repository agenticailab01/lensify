"""LlamaIndex adapter — surfaces indices, query engines, readers, settings.

Triggers on `llama_index` imports (the canonical package name). Extracts:

    - Index constructors (VectorStoreIndex, SummaryIndex, …)
    - Query/chat/retriever engines built via `.as_query_engine()` etc.
    - Document readers (SimpleDirectoryReader, PDFReader, …)
    - Global Settings assignments (llm, embed_model, chunk_size)

Output: ## LLAMA-INDEX capsule section.
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


_INDEX_RE = re.compile(
    r"""(\w+)\s*=\s*(VectorStoreIndex|SummaryIndex|KeywordTableIndex|"""
    r"""TreeIndex|KnowledgeGraphIndex|DocumentSummaryIndex)(?:\.\w+)?\s*\("""
)
_ENGINE_RE = re.compile(
    r"""(\w+)\s*=\s*[\w.]+\.\s*as_(query_engine|chat_engine|retriever)\s*\("""
)
_READER_RE = re.compile(
    r"""(\w+)\s*=\s*(SimpleDirectoryReader|PDFReader|WebReader|"""
    r"""DatabaseReader|NotionPageReader|SimpleWebPageReader|UnstructuredReader)\s*\("""
)
_SETTINGS_RE = re.compile(
    r"""Settings\s*\.\s*(llm|embed_model|node_parser|chunk_size|chunk_overlap|callback_manager)\s*="""
)


class LlamaIndexAdapter(FrameworkAdapter):
    name = "llamaindex"
    detect_signatures = ("import llama_index", "from llama_index")
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["llama_index"]

        entries: list[FrameworkEntry] = []
        settings_keys: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "llama_index"):
            for m in _INDEX_RE.finditer(text):
                entries.append(_entry("index", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _ENGINE_RE.finditer(text):
                kind_label = f"as_{m.group(2)}"
                entries.append(_entry("engine", m.group(1), kind_label,
                                      rel_path, line_of(text, m.start())))
            for m in _READER_RE.finditer(text):
                entries.append(_entry("reader", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _SETTINGS_RE.finditer(text):
                settings_keys.add(m.group(1))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["settings"] = sorted(settings_keys)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("settings"):
            return None
        lines = ["## LLAMA-INDEX"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        settings = info.meta.get("settings") or []
        if settings:
            lines.append(f"- config: {', '.join(settings)}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": cls},
    )
