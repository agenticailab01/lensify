"""LangChain adapter — surfaces chains, prompts, agents and tools.

Triggers on any langchain* import. Extracts the structural skeleton an
agent needs to reason about a RAG / agentic pipeline:

    - Prompt templates (ChatPromptTemplate, PromptTemplate)
    - Chains: pipe expressions (LCEL) AND named-class chains (LLMChain etc.)
    - Agent constructors (create_react_agent, AgentExecutor, …)
    - @tool decorated callables

Output: ## CHAINS capsule section, ordered by file/line. Confidence is
EXTRACTED when the regex matches a clear pattern; pipe-expression chains
are tagged INFERRED because LCEL syntax is overloaded.
"""
from __future__ import annotations

import re

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:  # script-style fallback
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


_PROMPT_RE = re.compile(
    r"""(\w+)\s*=\s*(ChatPromptTemplate|PromptTemplate|MessagesPlaceholder)(?:\.\w+)?\s*\("""
)
_CHAIN_CTOR_RE = re.compile(
    r"""(\w+)\s*=\s*(LLMChain|RetrievalQA|ConversationalRetrievalChain|"""
    r"""MultiPromptChain|SequentialChain|SimpleSequentialChain|TransformChain)\s*\("""
)
# LCEL pipe expression: `name = prompt | llm | parser`. Permissive — allows
# lambdas, commas, etc. between pipes; require RHS of `|` to start with a
# name/paren/bracket to avoid catching bitwise OR in numeric expressions.
_PIPE_RE = re.compile(
    r"""^[ \t]*(\w+)\s*=\s*[^|\n]+?\s*\|\s*[\w.(\[][^|\n]*(?:\s*\|\s*[^|\n]+)*""",
    re.M,
)
_AGENT_RE = re.compile(
    r"""(\w+)\s*=\s*(create_react_agent|create_openai_tools_agent|"""
    r"""create_structured_chat_agent|create_tool_calling_agent|AgentExecutor)\s*\("""
)
_TOOL_DECO_RE = re.compile(
    r"""@\s*tool(?:\s*\([^)]*\))?\s*\n+\s*(?:async\s+)?def\s+(\w+)"""
)


class LangChainAdapter(FrameworkAdapter):
    """Extract prompts, chains, agents, tools from a LangChain project."""

    name = "langchain"
    detect_signatures = (
        "import langchain", "from langchain",
        "import langchain_core", "from langchain_core",
        "import langchain_community", "from langchain_community",
        "import langchain_openai", "from langchain_openai",
    )
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["langchain"]

        entries: list[FrameworkEntry] = []
        for rel_path, text in iter_python_with(parsed_files, walk_result, "langchain"):
            for m in _PROMPT_RE.finditer(text):
                entries.append(_entry("prompt", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _CHAIN_CTOR_RE.finditer(text):
                entries.append(_entry("chain", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _PIPE_RE.finditer(text):
                # Filter out trivial `x = y | z` like boolean OR — require '|' twice
                if text[m.start():m.end()].count("|") >= 1:
                    entries.append(_entry("chain", m.group(1), "LCEL pipe",
                                          rel_path, line_of(text, m.start()),
                                          confidence="INFERRED"))
            for m in _AGENT_RE.finditer(text):
                entries.append(_entry("agent", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _TOOL_DECO_RE.finditer(text):
                entries.append(_entry("tool", m.group(1), "@tool",
                                      rel_path, line_of(text, m.start())))

        # Deterministic order: by path then line
        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["counts"] = _count_by_kind(info.entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## CHAINS"]
        for e in info.entries:
            tag = e.meta.get("class", e.signature)
            lines.append(f"- {e.kind} `{e.name}` — {tag}  ({e.path}:{e.line})")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int,
           confidence: str = "EXTRACTED") -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence=confidence,
        meta={"class": cls},
    )


def _count_by_kind(entries: list[FrameworkEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entries:
        counts[e.kind] = counts.get(e.kind, 0) + 1
    return counts
