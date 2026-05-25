# Framework adapter SDK

A complete contributor guide for adding framework support to ProjectLens. Read this top to bottom before writing your first adapter.

## TL;DR

A framework adapter is a single Python module (~80-120 LOC) that:
- **Detects** when a project uses your framework (O(1), imports-only)
- **Extracts** structural records from files that use it
- **Renders** a capsule section the agent sees on every scan

Built-in adapters live in `skills/projectlens/scripts/frameworks/<pack>/`. User-defined adapters drop into `<project>/.projectlens/frameworks/`.

## The contract

Every adapter inherits from `FrameworkAdapter` and must set 4 class attributes:

```python
class MyAdapter(FrameworkAdapter):
    name = "myframework"                   # Manifest key, unique across all adapters
    detect_signatures = (                  # Strings searched in parsed imports / file extensions
        "import myframework",
        "from myframework",
    )
    priority = PRIORITY_HIGH               # 0-100; capsule budget split by priority
    max_entries = 20                       # Hard cap (ABSOLUTE_MAX_ENTRIES = 50)
```

Three methods to implement (one is optional):

| Method | Required | Purpose |
|---|---|---|
| `detect(walk_result, parsed_files) -> bool` | Default OK for most | O(1) check — does the project use this framework? |
| `extract(walk_result, parsed_files) -> FrameworkInfo` | Yes | Walk the files, build structural records |
| `capsule_section(info, budget_tokens) -> str \| None` | Optional | Render a Markdown section for the capsule |

## Performance rules (CI-enforced)

| Rule | What | Enforced by |
|---|---|---|
| **R1** | Hook scripts (`dedup_hook.py`, `activity_hook.py`, etc.) never import `frameworks/*` | `test_hook_never_imports_frameworks` |
| **R2** | Adapter modules stay small (~80-120 LOC) | Code review |
| **R3** | `detect()` never opens files (no `open()`, `read_text()`, `read_bytes()`) | `test_adapter_detect_never_opens_files` |
| **R4** | `extract()` opens only files that match — use `iter_python_with()` | Code review |
| **R5** | `capsule_section()` respects `budget_tokens` — use `truncate()` | Code review |

Adding an adapter that violates R1 or R3 will fail the test suite. R2/R4/R5 are convention but routinely flagged.

## The two detection patterns

### Pattern 1: Import-based (most adapters)

For Python frameworks accessed via `import`. The default `detect()` checks `parsed_files` for matching imports. No override needed.

```python
class FastAPIAdapter(FrameworkAdapter):
    name = "fastapi"
    detect_signatures = ("import fastapi", "from fastapi")
    # Default detect() handles the rest
```

The registry normalises: `from fastapi.routing import APIRouter` parses to import `fastapi`, which matches the signature.

### Pattern 2: File-presence (notebooks, Vue, config files)

For frameworks that don't trigger on imports. Override `detect()` to check `walk_result.files`:

```python
class VueAdapter(FrameworkAdapter):
    name = "vue"
    detect_signatures = ("vue",)  # placeholder

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        for rec in walk_result.files:
            if getattr(rec, "language", None) == "Vue":
                return True
        return False
```

For this to be reachable, the registry's signal collector (`registry._collect_signals`) must emit a signal your `detect_signatures` matches. It currently emits:

- Top-level import names (lowercased) from parsed files
- File extensions present (without leading dot) — `.vue` → `vue`, `.ipynb` → `ipynb`
- For multi-dot config files like `tailwind.config.js`, the leading stem — `tailwind`
- Literal `docker-compose` when a Docker Compose file is found

If your trigger isn't one of these, extend `_collect_signals` accordingly.

## Writing `extract()`

The core extraction pattern uses `iter_python_with()` from the shared util:

```python
def extract(self, walk_result, parsed_files) -> FrameworkInfo:
    info = FrameworkInfo(name=self.name)
    info.detected_signatures = ["myframework"]

    entries: list[FrameworkEntry] = []
    for rel_path, text in iter_python_with(parsed_files, walk_result, "myframework"):
        for m in MY_REGEX.finditer(text):
            entries.append(FrameworkEntry(
                kind="endpoint",
                name=m.group(1),
                signature=f"Endpoint({m.group(2)!r})",
                path=rel_path,
                line=line_of(text, m.start()),
                confidence="EXTRACTED",
                meta={"some_data": "..."},
            ))
    entries.sort(key=lambda e: (e.path, e.line))
    info.entries = cap_entries(entries, self.max_entries)
    return info
```

**Why `iter_python_with()`:** it filters Python files to those that actually import your framework *before* reading them from disk. In a typical AI codebase, only ~5-20% of files import any given framework, so I/O drops by 80%+.

**For non-Python adapters** (config files, `.vue`, etc.), iterate `walk_result.files` directly and read what you need:

```python
for rec in walk_result.files:
    if Path(rec.path).name not in MY_CONFIG_NAMES:
        continue
    text = Path(rec.abs_path).read_text(encoding="utf-8", errors="ignore")
    # ... parse ...
```

## Multi-kwarg regex gotcha

⚠️ **This bit a real adapter.** Combining `[^)]*?` non-greedy with optional capture groups collapses to zero-width matches:

```python
# DOES NOT WORK: dimension and metric will be None even when present
_BAD = re.compile(
    r"""create_index\s*\(\s*['"]([^'"]+)['"]"""
    r"""[^)]*?(?:dimension\s*=\s*(\d+))?"""
    r"""[^)]*?(?:metric\s*=\s*['"]([^'"]+)['"])?""",
    re.S,
)
```

The non-greedy `[^)]*?` prefers to match zero, the optional group then prefers to skip, and you get the name but lose dimension/metric.

**Fix: two-step pattern.** Capture the args block, then run separate regexes per kwarg:

```python
_CALL_RE = re.compile(r"""create_index\s*\(([^)]*)\)""", re.S)
_NAME_RE = re.compile(r"""(?:^|\s|,)\s*(?:name\s*=\s*)?['"]([^'"]+)['"]""")
_DIM_RE = re.compile(r"""dimension\s*=\s*(\d+)""")
_METRIC_RE = re.compile(r"""metric\s*=\s*['"]([^'"]+)['"]""")

for m in _CALL_RE.finditer(text):
    body = m.group(1) or ""
    name_m = _NAME_RE.search(body)
    dim_m = _DIM_RE.search(body)
    metric_m = _METRIC_RE.search(body)
```

## Writing `capsule_section()`

```python
def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
    if not info.entries:
        return None
    lines = ["## MYFRAMEWORK"]
    for e in info.entries:
        lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
    return truncate("\n".join(lines), budget_tokens)
```

Format conventions:
- Section header: `## NAME` (uppercase, descriptive, no emoji)
- Entry bullets: `` - kind `name` — signature  (path:line) ``
- Trailing summary bullets when you have meta to surface (`- ops: x×3, y×1`)
- Always pass through `truncate(text, budget_tokens)` to enforce caller's budget

The budget gets split *proportional to priority* across active adapters. A typical T2 framework slot is 400 tokens shared by all detected adapters; high-priority adapters get a bigger slice. With 8+ adapters active, expect ~50-80 tokens each — design output for that envelope.

## Confidence tags

Every `FrameworkEntry` carries a confidence string. Agents reading the capsule use this to calibrate trust:

| Tag | When to use |
|---|---|
| `EXTRACTED` | Clean regex match against an unambiguous pattern |
| `INFERRED` | Heuristic match (e.g. LangChain LCEL pipe expressions — `\|` is overloaded) |
| `AMBIGUOUS` | Partial match; could be wrong (e.g. notebook with parse error) |

Don't over-use `EXTRACTED`. If your regex is fuzzy, tag the entries `INFERRED`.

## Manifest registration

Add an entry to `skills/projectlens/scripts/frameworks/manifest.json`:

```json
"myframework": {
  "pack": "_mypack",
  "module": "_mypack.myframework",
  "signatures": ["import myframework", "from myframework"]
}
```

The registry uses these signatures to pre-filter — it only `import`s your adapter module when at least one signature matches the project's parsed imports/files. Cost of an unused adapter: zero.

## Testing your adapter

Create `tests/test_<pack>_adapters.py`. Use the existing tests as templates — every pack has one. Minimum coverage per adapter:

- `test_<x>_detect` — positive case
- `test_<x>_extract` — verify all kinds + meta fields
- `test_<x>_capsule` — section renders, contains expected substrings
- `test_adapter_validate_class` — passes base class self-check (parameterised)
- `test_adapter_skips_unrelated_project` — empty project yields no entries

Run the suite:

```bash
python3 -m pytest tests/ -q
python3 -m pytest tests/benchmark_perf.py -q   # MUST stay green
```

The perf harness will catch:
- R1 violations (hook imports frameworks)
- R3 violations (`detect` opens files)
- SKILL.md growth past 8 KB
- Locked tier budgets changing without test update

## User-defined adapters (no plugin fork needed)

Drop adapter modules in `<your-project>/.projectlens/frameworks/`. They're auto-discovered per-scan. The loader:

- Skips files starting with `_` (so `_helpers.py` is safe)
- Imports each `.py` file and looks for `FrameworkAdapter` subclasses
- Catches any exception silently — a bad user adapter never breaks the scan

This is the recommended path for org-specific frameworks (internal SDKs, proprietary tools, etc.) that shouldn't ship in the public plugin.

## Reference: existing adapters

Use these as templates — each is ~80-120 LOC and shows a different pattern:

| Adapter | Pack | Pattern |
|---|---|---|
| `fastapi.py` | `_enterprise` | Standard import-based, reads source for route decorators |
| `jupyter.py` | `_notebooks` | File-presence (`.ipynb`), separate JSON parser |
| `langchain.py` | `_ai_apps` | Multiple kinds (prompt/chain/agent/tool), LCEL with INFERRED confidence |
| `pytorch.py` | `_ml_core` | Multi-kind extraction + training-loop heuristic |
| `transformers.py` | `_ml_core` | Captures string args (`checkpoint`) into meta |
| `vue.py` | `_enterprise` | File-presence + per-file SFC parsing |
| `docker_compose.py` | `_enterprise` | Indent-aware YAML walker (no PyYAML dep) |

The `_template/` directory contains a self-contained minimal adapter — copy it to start.

## Troubleshooting

**My adapter doesn't run.** Check manifest signatures match the project's signals:

```python
# In a Python REPL inside the plugin root:
from scripts.walker import walk
from scripts.ast_parser import parse_all
from scripts.frameworks.registry import _collect_signals

wr = walk("/path/to/project")
parsed = parse_all(wr.code_files)
print(_collect_signals(parsed, walk_result=wr))
```

If your signature keyword isn't in that set, your adapter won't match.

**Capsule section gets truncated.** You're competing for the framework budget. Make output denser, or bump the adapter's priority.

**Tests fail with "perf budget exceeded".** Your `extract()` is too slow or reads too many files. Profile with `python3 -m cProfile -o out.prof skills/projectlens/scripts/scan.py /path/to/project`.

**Hook startup tests fail after your change.** You imported something heavy into a hook script transitively. Don't import `frameworks/*` in hooks — Rule R1.
