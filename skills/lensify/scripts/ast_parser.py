"""Lightweight AST + regex parser.

- Python (.py): uses stdlib `ast` for accurate imports/classes/functions.
- All other languages: regex-based extraction. Coverage > accuracy is the goal —
  we want a coarse module-level signal, not a full call graph.

Output is a list of ParsedFile records that downstream stages consume.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .walker import FileRecord
except ImportError:
    from walker import FileRecord  # type: ignore[no-redef]


@dataclass
class ParsedFile:
    path: str
    language: str
    imports: list[str] = field(default_factory=list)   # imported module names
    exports: list[str] = field(default_factory=list)   # symbols this file defines
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    docstring: str | None = None                       # top-of-file docstring/comment

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "language": self.language,
            "imports": self.imports,
            "exports": self.exports,
            "classes": self.classes,
            "functions": self.functions,
            "docstring": (self.docstring or "")[:300] if self.docstring else None,
        }


def parse_python(record: FileRecord) -> ParsedFile:
    """Parse a Python file via stdlib ast."""
    p = ParsedFile(path=record.path, language="Python")
    try:
        source = Path(record.abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return p
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return p
    p.docstring = ast.get_docstring(tree)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                p.imports.append(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                p.imports.append(node.module.split(".")[0])
        elif isinstance(node, ast.ClassDef):
            p.classes.append(node.name)
            p.exports.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                p.functions.append(node.name)
                p.exports.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                p.functions.append(node.name)
                p.exports.append(node.name)
    return p


# Regex patterns for non-Python languages. Imperfect on purpose — we want speed
# and broad coverage, not parser-grade accuracy.
JS_IMPORT_RE = re.compile(r"""(?:import\s+(?:[\w*{}\s,]+\s+from\s+)?["']([^"']+)["'])|(?:require\(\s*["']([^"']+)["']\s*\))""")
JS_EXPORT_FN_RE = re.compile(r"""(?:export\s+)?(?:async\s+)?function\s+(\w+)""")
JS_EXPORT_CLASS_RE = re.compile(r"""(?:export\s+)?class\s+(\w+)""")
JS_EXPORT_CONST_RE = re.compile(r"""export\s+(?:const|let|var)\s+(\w+)""")

GO_IMPORT_RE = re.compile(r"""import\s+(?:\(([^)]*)\)|"([^"]+)")""", re.S)
GO_FUNC_RE = re.compile(r"""^func\s+(?:\([^)]+\)\s+)?([A-Z]\w*)\s*\(""", re.M)
GO_TYPE_RE = re.compile(r"""^type\s+([A-Z]\w*)\s+""", re.M)

JAVA_IMPORT_RE = re.compile(r"""import\s+([\w.]+);""")
JAVA_CLASS_RE = re.compile(r"""(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)""")

GENERIC_FUNC_RE = re.compile(r"""\bfunc\s+(\w+)|\bdef\s+(\w+)|\bfunction\s+(\w+)""")


def parse_javascript(record: FileRecord) -> ParsedFile:
    p = ParsedFile(path=record.path, language=record.language or "JavaScript")
    try:
        source = Path(record.abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return p
    for m in JS_IMPORT_RE.finditer(source):
        imp = m.group(1) or m.group(2)
        if imp:
            # Strip relative path prefix, keep the meaningful segment
            base = imp.split("/")[-1] if not imp.startswith(".") else imp
            p.imports.append(base)
    p.functions = JS_EXPORT_FN_RE.findall(source)
    p.classes = JS_EXPORT_CLASS_RE.findall(source)
    p.exports = list(set(p.functions + p.classes + JS_EXPORT_CONST_RE.findall(source)))
    return p


def parse_go(record: FileRecord) -> ParsedFile:
    p = ParsedFile(path=record.path, language="Go")
    try:
        source = Path(record.abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return p
    for m in GO_IMPORT_RE.finditer(source):
        block, single = m.group(1), m.group(2)
        if single:
            p.imports.append(single.split("/")[-1])
        elif block:
            for line in block.splitlines():
                line = line.strip().strip('"')
                if line and not line.startswith("//"):
                    p.imports.append(line.split("/")[-1])
    p.functions = GO_FUNC_RE.findall(source)
    p.classes = GO_TYPE_RE.findall(source)
    p.exports = list(set(p.functions + p.classes))
    return p


def parse_java(record: FileRecord) -> ParsedFile:
    p = ParsedFile(path=record.path, language="Java")
    try:
        source = Path(record.abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return p
    p.imports = [imp.split(".")[-1] for imp in JAVA_IMPORT_RE.findall(source)]
    p.classes = JAVA_CLASS_RE.findall(source)
    p.exports = list(p.classes)
    return p


def parse_generic(record: FileRecord) -> ParsedFile:
    """Fallback regex-only parser for any language with func/def/function keywords."""
    p = ParsedFile(path=record.path, language=record.language or "Unknown")
    try:
        source = Path(record.abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return p
    for m in GENERIC_FUNC_RE.finditer(source):
        name = m.group(1) or m.group(2) or m.group(3)
        if name and not name.startswith("_"):
            p.functions.append(name)
    p.exports = list(set(p.functions))
    return p


# Dispatcher
PARSERS = {
    "Python": parse_python,
    "JavaScript": parse_javascript,
    "TypeScript": parse_javascript,
    "Go": parse_go,
    "Java": parse_java,
}


def parse_file(record: FileRecord) -> ParsedFile:
    """Dispatch to the right parser based on language."""
    if not record.is_code:
        return ParsedFile(path=record.path, language=record.language or "Unknown")
    parser = PARSERS.get(record.language or "")
    if parser is None:
        return parse_generic(record)
    return parser(record)


def parse_all(records: list[FileRecord]) -> list[ParsedFile]:
    """Parse every code file in the list."""
    return [parse_file(r) for r in records if r.is_code]


def detect_entry_points(parsed: list[ParsedFile]) -> list[dict]:
    """Best-effort entry point detection.

    Heuristics:
      - Python: file with `if __name__ == "__main__"` or main() function
      - JS: files named index.{js,ts,jsx,tsx} at root, or scripts in package.json
      - Anything called main.* or app.* or server.* at the root
    """
    entries: list[dict] = []
    seen: set[str] = set()
    for p in parsed:
        name = p.path.split("/")[-1].lower()
        depth = p.path.count("/")
        looks_like_entry = False
        role = None
        if name in ("main.py", "app.py", "server.py", "manage.py", "cli.py", "run.py"):
            looks_like_entry = True
            role = name.replace(".py", "")
        elif name.startswith("index.") and depth <= 2:
            looks_like_entry = True
            role = "index"
        elif name in ("main.go", "main.rs", "main.java"):
            looks_like_entry = True
            role = "main"
        elif "main" in p.functions and p.language == "Python":
            looks_like_entry = True
            role = "main()"
        if looks_like_entry and p.path not in seen:
            entries.append({"path": p.path, "role": role or "entry"})
            seen.add(p.path)
    return entries


def detect_shape(parsed: list[ParsedFile], top_dirs: list[str]) -> dict:
    """Pick a diagram shape based on import patterns and top-level directories.

    Returns: {"shape": "layered"|"hub-spoke"|"pipeline"|"domain-map"|"flat",
              "confidence": "strong"|"weak"|"forced", "evidence": [...] }
    """
    evidence: list[str] = []
    score = {"layered": 0, "hub-spoke": 0, "pipeline": 0, "domain-map": 0}

    # Layered signals
    layered_names = {"api", "domain", "core", "db", "repository", "models", "presentation", "infrastructure"}
    layer_hits = sum(1 for d in top_dirs if d.lower() in layered_names)
    if layer_hits >= 2:
        score["layered"] += layer_hits
        evidence.append(f"layered-named dirs: {[d for d in top_dirs if d.lower() in layered_names]}")

    # Pipeline signals
    pipeline_names = {"ingest", "extract", "transform", "load", "process", "validate", "publish"}
    pipe_hits = sum(1 for d in top_dirs if d.lower() in pipeline_names)
    if pipe_hits >= 2:
        score["pipeline"] += pipe_hits
        evidence.append(f"pipeline-named dirs: {[d for d in top_dirs if d.lower() in pipeline_names]}")

    # Domain-map signals (monorepo with many top-level packages)
    if len(top_dirs) >= 5 and any(d in ("services", "apps", "packages") for d in top_dirs):
        score["domain-map"] += 3
        evidence.append("monorepo with services/apps/packages at root")

    # Hub-spoke detection: is one module imported by ≥ 50% of others?
    import_counts: dict[str, int] = {}
    for p in parsed:
        for imp in set(p.imports):
            import_counts[imp] = import_counts.get(imp, 0) + 1
    if parsed:
        threshold = len(parsed) * 0.5
        hubs = [name for name, n in import_counts.items() if n >= threshold]
        if hubs:
            score["hub-spoke"] += len(hubs)
            evidence.append(f"hub modules: {hubs[:3]}")

    # Pick winner
    if not any(score.values()):
        return {"shape": "flat", "confidence": "forced", "evidence": ["no clear shape signals"]}
    winner = max(score, key=score.get)
    top = score[winner]
    confidence = "strong" if top >= 3 else "weak"
    return {"shape": winner, "confidence": confidence, "evidence": evidence}
