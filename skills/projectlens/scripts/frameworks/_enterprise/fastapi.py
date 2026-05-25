"""FastAPI adapter — reference implementation of the FrameworkAdapter contract.

Detects FastAPI usage by `import fastapi` / `from fastapi`, then walks parsed
Python files looking for route decorator patterns and surfaces them as
FrameworkEntry records.

Recognised patterns:
    @app.get("/users")
    @router.post("/items/{id}")
    @app.api_route("/x", methods=["GET", "POST"])
    @router.delete("/y", response_model=Foo)

Output: a `ROUTES` capsule section listing up to max_entries routes,
ordered by path. Each entry includes method, path, source path:line.

This file is deliberately ~100 lines + the regex set — every adapter should
look this small. Anything bigger is a design smell.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
except ImportError:  # script-style import (when frameworks/ isn't a package)
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )


# Pattern: @<thing>.<verb>(<args>)
# Captures: 1=verb, 2=raw-args-up-to-closing-paren-on-same-line
_ROUTE_DECORATOR_RE = re.compile(
    r"""@\s*\w+\s*\.\s*(get|post|put|delete|patch|head|options|api_route)\s*\(([^)]*)\)""",
    re.IGNORECASE,
)
# Extract the path: first quoted string in the args
_PATH_LITERAL_RE = re.compile(r"""["']([^"']+)["']""")


HTTP_VERBS = {"get", "post", "put", "delete", "patch", "head", "options"}


class FastAPIAdapter(FrameworkAdapter):
    """FastAPI route extractor."""

    name = "fastapi"
    detect_signatures = ("import fastapi", "from fastapi")
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["fastapi"]

        entries: list[FrameworkEntry] = []

        # Walk only Python files (FastAPI is Python).
        for pf in parsed_files:
            if (pf.language or "").lower() != "python":
                continue
            try:
                source = Path(pf.path).resolve()  # rel path won't open; need abs
                # parsed_files records have abs paths via the walker — but
                # ParsedFile only stores `path` (relative). We read the file
                # from the walker's view via a quick lookup.
                continue_outer = False
            except Exception:
                continue_outer = True
            if continue_outer:
                continue
            # The walker provides abs paths on FileRecord; locate it
            abs_path = self._abs_path_for(walk_result, pf.path)
            if not abs_path:
                continue
            try:
                text = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            self._scan_file(text, pf.path, entries)

        entries = cap_entries(entries, self.max_entries)
        # Stable-sort by path for deterministic capsule output
        entries.sort(key=lambda e: (e.meta.get("path", ""), e.meta.get("method", "")))
        info.entries = entries
        info.meta["routes_total"] = len(entries)
        return info

    @staticmethod
    def _abs_path_for(walk_result, rel_path: str) -> str | None:
        for rec in walk_result.files:
            if rec.path == rel_path:
                return rec.abs_path
        return None

    @staticmethod
    def _scan_file(text: str, rel_path: str, out: list[FrameworkEntry]) -> None:
        for m in _ROUTE_DECORATOR_RE.finditer(text):
            verb = m.group(1).lower()
            raw_args = m.group(2) or ""
            # Locate the path literal
            path_m = _PATH_LITERAL_RE.search(raw_args)
            if not path_m:
                continue
            url_path = path_m.group(1)
            # Compute line number
            line = text[: m.start()].count("\n") + 1
            if verb == "api_route":
                # methods kwarg may list multiple verbs
                methods = re.findall(r"['\"](\w+)['\"]", raw_args)
                methods = [v.upper() for v in methods if v.lower() in HTTP_VERBS] or ["ANY"]
                for vb in methods:
                    out.append(_make_entry(vb, url_path, rel_path, line))
            else:
                out.append(_make_entry(verb.upper(), url_path, rel_path, line))

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## ROUTES"]
        for e in info.entries:
            method = e.meta.get("method", "?")
            url = e.meta.get("path", "?")
            lines.append(f"- `{method} {url}`  ({e.path}:{e.line})")
        out = "\n".join(lines)
        # Enforce caller's token budget — same truncate logic as capsule.py uses
        from importlib import import_module
        try:
            cap_mod = import_module("scripts.capsule")
        except ImportError:
            try:
                cap_mod = import_module("capsule")
            except ImportError:
                return out
        return cap_mod.truncate_to_tokens(out, budget_tokens)


def _make_entry(method: str, url: str, rel_path: str, line: int) -> FrameworkEntry:
    return FrameworkEntry(
        kind="route",
        name=f"{method} {url}",
        signature=f"{method} {url}",
        path=rel_path,
        line=line,
        confidence="EXTRACTED",
        meta={"method": method, "path": url},
    )
