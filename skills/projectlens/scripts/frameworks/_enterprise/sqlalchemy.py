"""SQLAlchemy adapter — surfaces ORM models, engines, sessions.

Triggers on `sqlalchemy` imports. Extracts:

    - Declarative model classes (both 1.x `declarative_base()` subclasses
      and 2.x `DeclarativeBase` subclasses)
    - __tablename__ values per model
    - Column(...) definitions per model
    - relationship(...) declarations (foreign-key links between models)
    - create_engine(...) and sessionmaker(...) / Session() construction

Output: ## SQLALCHEMY capsule section listing models with their tables +
column counts, plus engine/session entries.
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


# Matches classes that inherit from a base name — `Base`, `DeclarativeBase`,
# `db.Model` (Flask-SQLAlchemy), or any name ending in `Base`.
_MODEL_RE = re.compile(
    r"""class\s+(\w+)\s*\(\s*([\w.]+)\s*\)\s*:"""
)
_BASES_OK = re.compile(r"""(^|\.)(Base|DeclarativeBase|Model)$""")
_TABLENAME_RE = re.compile(
    r"""__tablename__\s*=\s*['"]([^'"]+)['"]"""
)
_COLUMN_RE = re.compile(
    r"""(\w+)\s*(?::\s*Mapped\[[^\]]+\])?\s*=\s*(?:mapped_column|Column)\s*\("""
)
_REL_RE = re.compile(
    r"""(\w+)\s*(?::\s*[\w\[\], ]+)?\s*=\s*relationship\s*\(\s*['"]?([\w.]+)?"""
)
_ENGINE_RE = re.compile(
    r"""(\w+)\s*=\s*(?:create_engine|create_async_engine)\s*\(\s*['"]?([^'",\)]+)?"""
)
_SESSION_RE = re.compile(
    r"""(\w+)\s*=\s*(sessionmaker|async_sessionmaker|Session|scoped_session)\s*\("""
)


class SQLAlchemyAdapter(FrameworkAdapter):
    name = "sqlalchemy"
    detect_signatures = ("import sqlalchemy", "from sqlalchemy")
    priority = PRIORITY_HIGH
    max_entries = 30

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["sqlalchemy"]

        entries: list[FrameworkEntry] = []
        tables: set[str] = set()
        relationships: list[tuple[str, str]] = []  # (source_model, target)

        for rel_path, text in iter_python_with(parsed_files, walk_result, "sqlalchemy"):
            # First find ORM classes — those inheriting Base / DeclarativeBase / Model
            for m in _MODEL_RE.finditer(text):
                cls = m.group(1)
                parent = m.group(2)
                if not _BASES_OK.search(parent):
                    continue
                # Find tablename + columns in this class body (next ~3 KB)
                body = text[m.end(): m.end() + 3000]
                tn_m = _TABLENAME_RE.search(body)
                tname = tn_m.group(1) if tn_m else "?"
                if tname != "?":
                    tables.add(tname)
                col_count = len(_COLUMN_RE.findall(body))
                rels_here = [(cls, rm.group(2) or "?") for rm in _REL_RE.finditer(body)]
                relationships.extend(rels_here)
                entries.append(FrameworkEntry(
                    kind="model",
                    name=cls,
                    signature=f"class {cls}({parent}) → table {tname}",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={
                        "class": cls,
                        "tablename": tname,
                        "columns": col_count,
                        "relationships": [r[1] for r in rels_here],
                    },
                ))

            for m in _ENGINE_RE.finditer(text):
                url = (m.group(2) or "").strip().rstrip("'\"")
                # Redact passwords from URL for safety
                if url and "://" in url:
                    url = re.sub(r"://[^@/]*@", "://***@", url)
                entries.append(FrameworkEntry(
                    kind="engine",
                    name=m.group(1),
                    signature=f"create_engine({url or '?'})",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": "engine", "url": url},
                ))
            for m in _SESSION_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="session",
                    name=m.group(1),
                    signature=m.group(2),
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(2)},
                ))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["tables"] = sorted(tables)
        info.meta["relationships"] = relationships[:20]
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## SQLALCHEMY"]
        for e in info.entries:
            extra = ""
            if e.kind == "model":
                cols = e.meta.get("columns", 0)
                extra = f" · {cols} cols"
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}{extra}  ({e.path}:{e.line})")
        rels = info.meta.get("relationships") or []
        if rels:
            shown = ", ".join(f"{a}→{b}" for a, b in rels[:5])
            lines.append(f"- relationships: {shown}")
        return truncate("\n".join(lines), budget_tokens)
