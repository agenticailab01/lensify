# Adapter SDK template

This is the **starting point for new framework adapters**. Copy this directory to begin.

## Quick start

```bash
# 1. Copy template to your pack name
cp -r _template _myframework

# 2. Rename and edit
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes

# 3. Register in the manifest
$EDITOR ../manifest.json
```

Add a manifest entry:

```json
"myframework": {
  "pack": "_myframework",
  "module": "_myframework.myframework",
  "signatures": ["import myframework", "from myframework"]
}
```

```bash
# 4. Copy + adapt the test file
cp ../../../../../tests/test_fastapi_adapter.py ../../../../../tests/test_myframework.py
$EDITOR ../../../../../tests/test_myframework.py

# 5. Run the suite — everything must stay green
python3 -m pytest tests/ -q
python3 -m pytest tests/benchmark_perf.py -q
```

## Contract reminder

| Rule | What |
|---|---|
| R1 | Hook scripts never import `frameworks/*` (perf harness enforces) |
| R2 | Adapter file is ≤ ~120 LOC — anything bigger is a smell |
| R3 | `detect()` is O(1) — never opens files |
| R4 | `extract()` opens only files matching your framework's import |
| R5 | `capsule_section()` respects `budget_tokens` via `truncate()` |

## Design tips

**Use `iter_python_with(parsed_files, walk_result, marker)`** — it yields `(rel_path, source_text)` only for files that import `marker`. In a typical AI codebase, only ~5-20% of files import any given framework, so this cuts disk I/O by 80%+.

**For non-Python frameworks** (config files, `.vue`, etc.), override `detect()` to check `walk_result.files` for the relevant extension or basename, then iterate over those records directly in `extract()`.

**For multi-kwarg parsing**, capture the args block first then run separate small regexes for each kwarg. Combining `[^)]*?` non-greedy with optional groups collapses to zero-width matches — this was a real bug fixed during the `_vector_db` pack.

**Confidence tags:**
- `EXTRACTED` — clear, unambiguous regex match
- `INFERRED` — heuristic match (e.g. LCEL pipe expressions in LangChain)
- `AMBIGUOUS` — partial match, possibly wrong

Agents reading the capsule use these tags to calibrate their trust.

See `references/adapter-sdk.md` for the full contract, perf rules, and troubleshooting.
