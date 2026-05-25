# Tool-Output Compression (Phase 6)

ProjectLens v0.5.0 ships a PostToolUse hook that detects large textual tool
outputs (Bash dumps, web fetches, browser snapshots) and emits a
type-specific compressed summary into the conversation alongside the raw
output. The raw output is preserved on disk so the agent can retrieve it
on demand.

This closes the gap with Context Mode (315KB → 5KB on session captures).

## Detected output types

The detector picks one of these labels:

| Type | Detected by | Compressor output |
|---|---|---|
| `html` | `<html`/`<body`/`<title>` tags | title + headings + first paragraph + char count |
| `json` | starts with `{`/`[`, parses cleanly | schema sketch + top-level keys + first item |
| `pytest` | `== test session ==`/`passed`/`FAILED` markers | totals + failing test list |
| `playwright` | `[role=` / `accessibility-tree` markers | role counts + page title |
| `log` | many log-shaped lines (timestamp/level) | per-level counts + first errors |
| `trace` | Traceback / panic / `at File:line` | error message + top frames |
| `diff` | `diff --git`/`+++`/`---` markers | per-file +/- counts |
| `tabular` | multi-line delimited columns | header + sample rows |
| `text` | none of the above | head/middle/tail snippets |

If the output is < 2 KB it passes through unchanged (no value in compressing
short outputs).

## Compression ratios (typical)

| Input | Original | Compressed | Ratio |
|---|---|---|---|
| 56 KB Playwright snapshot | 56,000 | 300-600 bytes | **~100×** |
| 47 KB GitHub issues JSON | 47,000 | 800-1,200 bytes | **~40×** |
| 28 KB pytest verbose output | 28,000 | 400 bytes | **~70×** |
| 15 KB nginx access log | 15,000 | 500 bytes | **~30×** |
| 8 KB stack trace | 8,000 | 600 bytes | **~13×** |
| 4 KB random text (fallback) | 4,000 | 1,500 bytes | **~3×** |

Stack traces and free-form text compress less aggressively because they're
already information-dense. The big wins are HTML/JSON/Playwright/log dumps
where most of the bytes are structural noise.

## How it appears to the agent

After a Bash call like `pytest -v` that produced 28 KB of output, the agent
also sees, attached via `additionalContext`:

```
[ProjectLens] Tool output (28,341 bytes, detected as `pytest`) —
compressed to 412 bytes (68.8× ratio).

Summary:
pytest output — 47 passed, **3 failed**, 0 skipped
Failing tests:
  - tests/test_auth.py::test_jwt_expiry
  - tests/test_auth.py::test_refresh
  - tests/test_billing.py::test_currency_rounding

Full raw output saved to `.projectlens-outputs/3f8a2c1b9d04.txt`.
Read it back only if the summary is insufficient.
```

The agent now has both: the raw output (in case it needs literal text) and
a structured summary (which is what subsequent turns will reference).

## Where the savings land

Unlike MCP-based compressors (Context Mode, Claude-Mem), this hook cannot
suppress the raw output from the current turn — Claude Code hooks are
add-only. The savings come from three places:

1. **Subsequent-turn references**: when the agent later asks "what did pytest
   say?" it refers to our 400-byte summary, not the 28 KB raw output.
2. **Auto-compaction survival**: when Claude Code auto-compacts the
   conversation, our `additionalContext` block is preserved while the raw
   tool result is summarised lossily. Our summary is what survives.
3. **Statusline / telemetry**: each compression event is recorded in
   `session_state.compressions` so the user sees cumulative savings.

For users who want MCP-level interception, ProjectLens stacks cleanly with
Context Mode — install both, and Context Mode handles the immediate-turn
compression while ProjectLens handles project orientation + session memory.

## File storage

Compressed-away raw outputs are stored at:

```
<project-root>/.projectlens-outputs/<sha256-12>.txt
```

The 12-char hash makes the path content-addressable; identical outputs share
storage. Files are never auto-deleted within a session.

Recommended `.gitignore` addition: `.projectlens-outputs/`.

## Opt out

```bash
export PROJECTLENS_COMPRESS_OUTPUT=0    # disable just compression
export PROJECTLENS_DEDUP=0              # disable ALL projectlens hooks
```

## What's NOT done

- Streaming compression of partial outputs (we wait for the full response)
- LLM-assisted compression for unknown types (deterministic only, by design)
- Binary file handling (we only touch text)
- Diff-aware compression for "this output is the same as last time" (Phase 6.1)
