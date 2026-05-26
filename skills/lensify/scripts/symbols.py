"""Symbol micro-snippets (Phase 5).

Extracts one-line signatures for the top-N most-referenced public symbols in
the project, scored by how often each defining module is imported by other
files. Saves ~300-450 tokens per "what's the signature of X?" question by
putting the answer directly in the capsule.

Strategy:
    1. For each parsed file, count how many OTHER files import it.
    2. Rank files by that count (popular files first).
    3. Harvest signatures from those files until we hit the symbol cap.
    4. Skip private symbols (those starting with _).

Why not full call-graph analysis? Two reasons:
    - It's expensive (quadratic in worst case)
    - The simple "imported by many" heuristic captures 80% of the value at
      <5% of the cost.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    from .ast_parser import ParsedFile
    from .walker import FileRecord
except ImportError:
    from ast_parser import ParsedFile  # type: ignore[no-redef]
    from walker import FileRecord  # type: ignore[no-redef]


@dataclass
class Symbol:
    """One extracted public symbol with its formatted signature."""
    name: str                   # the bare symbol name, e.g. "authenticate"
    signature: str              # one-line formatted form, e.g. "authenticate(email: str, pwd: str) -> Token | None"
    path: str                   # relative file path where it's defined
    line: int                   # line number (1-based)
    kind: str                   # "function" | "method" | "class" | "constant"
    score: int = 0              # ranking score (higher = more referenced)

    def to_dict(self) -> dict:
        return asdict(self)


# ---- Python (AST-based — most accurate) ----

def _annotation_to_str(node) -> str:
    """Best-effort serialise an AST annotation to a short string.

    Uses ast.unparse (Python 3.9+) when possible; falls back to attribute walks.
    """
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return getattr(node, "id", "?")


def _args_to_str(args: ast.arguments) -> str:
    """Render an ast.arguments node as `name: T, name2: U`."""
    parts: list[str] = []
    # positional-only
    for a in getattr(args, "posonlyargs", []) or []:
        ann = _annotation_to_str(a.annotation)
        parts.append(f"{a.arg}: {ann}" if ann else a.arg)
    # regular
    for a in args.args:
        if a.arg in ("self", "cls"):
            continue
        ann = _annotation_to_str(a.annotation)
        parts.append(f"{a.arg}: {ann}" if ann else a.arg)
    # *args
    if args.vararg:
        ann = _annotation_to_str(args.vararg.annotation)
        parts.append(f"*{args.vararg.arg}: {ann}" if ann else f"*{args.vararg.arg}")
    # **kwargs
    if args.kwarg:
        ann = _annotation_to_str(args.kwarg.annotation)
        parts.append(f"**{args.kwarg.arg}: {ann}" if ann else f"**{args.kwarg.arg}")
    return ", ".join(parts)


def extract_python_signatures(abs_path: str, rel_path: str) -> list[Symbol]:
    """Extract public function and class signatures from a Python file."""
    out: list[Symbol] = []
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return out

    # Top-level only (we don't descend into nested defs — they're internal helpers)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            args = _args_to_str(node.args)
            ret = _annotation_to_str(node.returns)
            sig = f"{node.name}({args})"
            if ret:
                sig += f" -> {ret}"
            out.append(Symbol(
                name=node.name, signature=sig, path=rel_path,
                line=node.lineno, kind="function",
            ))
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            bases_strs = []
            for b in node.bases:
                s = _annotation_to_str(b)
                if s:
                    bases_strs.append(s)
            sig = f"class {node.name}"
            if bases_strs:
                sig += f"({', '.join(bases_strs)})"
            out.append(Symbol(
                name=node.name, signature=sig, path=rel_path,
                line=node.lineno, kind="class",
            ))
            # Also surface up to 3 public methods per class
            method_count = 0
            for sub in node.body:
                if method_count >= 3:
                    break
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and not sub.name.startswith("_"):
                    args = _args_to_str(sub.args)
                    ret = _annotation_to_str(sub.returns)
                    msig = f"{node.name}.{sub.name}({args})"
                    if ret:
                        msig += f" -> {ret}"
                    out.append(Symbol(
                        name=f"{node.name}.{sub.name}", signature=msig,
                        path=rel_path, line=sub.lineno, kind="method",
                    ))
                    method_count += 1
    return out


# ---- JavaScript / TypeScript (regex — best-effort) ----

_JS_FUNC_RE = re.compile(
    r"""(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{;\n]+?))?(?=\s*[{;\n])""",
    re.MULTILINE,
)
_JS_CLASS_RE = re.compile(
    r"""(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{""",
    re.MULTILINE,
)
_JS_ARROW_RE = re.compile(
    r"""(?:export\s+)?(?:const|let)\s+(\w+)\s*(?::\s*[^=]+)?=\s*(?:async\s*)?\(([^)]*)\)\s*=>""",
    re.MULTILINE,
)


def extract_js_signatures(abs_path: str, rel_path: str) -> list[Symbol]:
    out: list[Symbol] = []
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return out

    for m in _JS_FUNC_RE.finditer(source):
        name = m.group(1)
        args = (m.group(2) or "").strip()
        ret = (m.group(3) or "").strip()
        if name.startswith("_"):
            continue
        sig = f"{name}({args})"
        if ret:
            sig += f" -> {ret}"
        line = source[: m.start()].count("\n") + 1
        out.append(Symbol(name=name, signature=sig, path=rel_path, line=line, kind="function"))

    for m in _JS_CLASS_RE.finditer(source):
        name = m.group(1)
        if name.startswith("_"):
            continue
        ext = m.group(2)
        sig = f"class {name}" + (f" extends {ext}" if ext else "")
        line = source[: m.start()].count("\n") + 1
        out.append(Symbol(name=name, signature=sig, path=rel_path, line=line, kind="class"))

    for m in _JS_ARROW_RE.finditer(source):
        name = m.group(1)
        args = (m.group(2) or "").strip()
        if name.startswith("_"):
            continue
        sig = f"{name} = ({args}) => …"
        line = source[: m.start()].count("\n") + 1
        out.append(Symbol(name=name, signature=sig, path=rel_path, line=line, kind="function"))

    return out


# ---- Go (regex — best-effort, exported names start with uppercase) ----

_GO_FUNC_RE = re.compile(
    r"""^func\s+(?:\(([^)]+)\)\s+)?([A-Z]\w*)\s*\(([^)]*)\)\s*([^\{]*?)\s*\{""",
    re.MULTILINE,
)
_GO_TYPE_RE = re.compile(r"""^type\s+([A-Z]\w*)\s+(struct|interface)""", re.MULTILINE)


def extract_go_signatures(abs_path: str, rel_path: str) -> list[Symbol]:
    out: list[Symbol] = []
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return out

    for m in _GO_FUNC_RE.finditer(source):
        receiver = (m.group(1) or "").strip()
        name = m.group(2)
        args = (m.group(3) or "").strip()
        ret = (m.group(4) or "").strip()
        full_name = name
        if receiver:
            # Receiver looks like "s *Service" or "s Service" — we want
            # the type name (the last token, with any leading `*` stripped).
            parts = receiver.split()
            if parts:
                type_name = parts[-1].lstrip("*")
                if type_name:
                    full_name = f"{type_name}.{name}"
        sig = f"func {full_name}({args})"
        if ret:
            sig += f" {ret}"
        line = source[: m.start()].count("\n") + 1
        out.append(Symbol(
            name=full_name, signature=sig, path=rel_path,
            line=line, kind="method" if receiver else "function",
        ))

    for m in _GO_TYPE_RE.finditer(source):
        name = m.group(1)
        kind = m.group(2)
        sig = f"type {name} {kind}"
        line = source[: m.start()].count("\n") + 1
        out.append(Symbol(name=name, signature=sig, path=rel_path, line=line, kind="class"))
    return out


# ---- Dispatcher ----

EXTRACTORS = {
    "Python": extract_python_signatures,
    "JavaScript": extract_js_signatures,
    "TypeScript": extract_js_signatures,
    "Go": extract_go_signatures,
}


def extract_signatures(record: FileRecord) -> list[Symbol]:
    """Dispatch by language. Returns [] for unsupported languages."""
    if not record.is_code or not record.language:
        return []
    extractor = EXTRACTORS.get(record.language)
    if extractor is None:
        return []
    return extractor(record.abs_path, record.path)


# ---- Scoring + top-N selection ----

def _module_name_from_path(rel_path: str) -> str:
    """Heuristic: a file's 'module name' is its filename without extension.

    This is what an `import X` statement typically references.
    """
    return Path(rel_path).stem


def rank_files_by_imports(parsed_files: list[ParsedFile]) -> dict[str, int]:
    """Count, per file path, how many OTHER files import its module."""
    # Map module-name → count of imports
    mod_count: dict[str, int] = {}
    for pf in parsed_files:
        for imp in pf.imports:
            base = imp.rstrip("./").split("/")[-1]
            mod_count[base] = mod_count.get(base, 0) + 1
    # Score each parsed file by mod_count of its filename
    scores: dict[str, int] = {}
    for pf in parsed_files:
        mod = _module_name_from_path(pf.path)
        scores[pf.path] = mod_count.get(mod, 0)
    return scores


def find_top_symbols(
    records: list[FileRecord],
    parsed_files: list[ParsedFile],
    top_n: int = 20,
) -> list[Symbol]:
    """Return up to top_n public symbols, sorted by source-file popularity."""
    file_scores = rank_files_by_imports(parsed_files)
    # Sort code files by (score desc, then path for determinism)
    records_sorted = sorted(
        [r for r in records if r.is_code],
        key=lambda r: (-file_scores.get(r.path, 0), r.path),
    )

    seen: set[str] = set()
    out: list[Symbol] = []
    for rec in records_sorted:
        if len(out) >= top_n:
            break
        score = file_scores.get(rec.path, 0)
        for sym in extract_signatures(rec):
            if sym.name in seen:
                continue
            sym.score = score
            seen.add(sym.name)
            out.append(sym)
            if len(out) >= top_n:
                break
    return out


def symbols_to_dicts(symbols: list[Symbol]) -> list[dict]:
    """Plain-dict form for lens.json serialisation."""
    return [s.to_dict() for s in symbols]
