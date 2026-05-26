"""LangGraph adapter — surfaces the agent state machine.

Triggers on `langgraph` imports. Extracts the *shape* of each graph:

    - StateGraph / MessageGraph constructor
    - .add_node("name", fn) calls
    - .add_edge / .add_conditional_edges
    - .set_entry_point / .set_finish_point
    - Checkpointer usage (MemorySaver / SqliteSaver)

The capsule section shows one entry per graph with its nodes + edges,
not one entry per node — agent state machines are most useful when seen
as a connected whole.
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


_GRAPH_CTOR_RE = re.compile(r"""(\w+)\s*=\s*(StateGraph|MessageGraph)\s*\(""")
_NODE_RE = re.compile(r"""\.\s*add_node\s*\(\s*["'](\w+)["']""")
_EDGE_RE = re.compile(r"""\.\s*add_edge\s*\(\s*["'](\w+)["']\s*,\s*["'](\w+)["']""")
_COND_EDGE_RE = re.compile(r"""\.\s*add_conditional_edges\s*\(\s*["'](\w+)["']""")
_ENTRY_RE = re.compile(r"""\.\s*set_entry_point\s*\(\s*["'](\w+)["']""")
_FINISH_RE = re.compile(r"""\.\s*set_finish_point\s*\(\s*["'](\w+)["']""")
_CHECKPOINT_RE = re.compile(r"""(MemorySaver|SqliteSaver|PostgresSaver|AsyncSqliteSaver)\s*\(""")


class LangGraphAdapter(FrameworkAdapter):
    name = "langgraph"
    detect_signatures = ("import langgraph", "from langgraph")
    priority = PRIORITY_HIGH
    max_entries = 10  # graphs, not nodes — agents project usually has 1-3

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["langgraph"]

        entries: list[FrameworkEntry] = []
        for rel_path, text in iter_python_with(parsed_files, walk_result, "langgraph"):
            graphs = list(_GRAPH_CTOR_RE.finditer(text))
            # All graph-modifying calls — collected once per file then attributed
            # to the most recent graph by name proximity.
            nodes = sorted({m.group(1) for m in _NODE_RE.finditer(text)})
            edges = [(m.group(1), m.group(2)) for m in _EDGE_RE.finditer(text)]
            cond_edges = sorted({m.group(1) for m in _COND_EDGE_RE.finditer(text)})
            entries_set = sorted({m.group(1) for m in _ENTRY_RE.finditer(text)})
            finish_set = sorted({m.group(1) for m in _FINISH_RE.finditer(text)})
            checkpointer = None
            cp_m = _CHECKPOINT_RE.search(text)
            if cp_m:
                checkpointer = cp_m.group(1)

            for m in graphs:
                entries.append(FrameworkEntry(
                    kind="graph",
                    name=m.group(1),
                    signature=m.group(2),
                    path=rel_path,
                    line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={
                        "class": m.group(2),
                        "nodes": nodes,
                        "edges": edges[:8],  # cap edges per graph
                        "cond_edges": cond_edges,
                        "entry": entries_set[0] if entries_set else None,
                        "finish": finish_set[0] if finish_set else None,
                        "checkpointer": checkpointer,
                    },
                ))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## LANGGRAPH"]
        for e in info.entries:
            m = e.meta
            lines.append(f"- graph `{e.name}` — {m.get('class')}  ({e.path}:{e.line})")
            nodes = m.get("nodes") or []
            if nodes:
                lines.append(f"  - nodes: {', '.join(nodes[:8])}")
            edges = m.get("edges") or []
            if edges:
                arrows = ", ".join(f"{a}→{b}" for a, b in edges[:5])
                lines.append(f"  - edges: {arrows}")
            cond = m.get("cond_edges") or []
            if cond:
                lines.append(f"  - conditional from: {', '.join(cond[:4])}")
            entry, finish = m.get("entry"), m.get("finish")
            if entry or finish:
                lines.append(f"  - entry: {entry or '?'} · finish: {finish or '?'}")
            cp = m.get("checkpointer")
            if cp:
                lines.append(f"  - checkpointer: {cp}")
        return truncate("\n".join(lines), budget_tokens)
