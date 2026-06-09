# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Lensify is

Lensify produces a single-page adaptive project lens (HTML) plus a token-optimized
context capsule (Markdown) for any codebase, and ships a set of session hooks that cut
orientation/context tokens by 70-90%. **Pure Python stdlib — zero runtime dependencies.**
It is distributed through four channels that all share one scan engine.

## Repository layout (where things actually live)

The Python source is NOT at repo root — it lives inside the plugin tree:

```
plugins/lensify/skills/lensify/scripts/   ← all engine + hook source (the real code)
plugins/lensify/skills/lensify/SKILL.md   ← skill contract / sub-commands
plugins/lensify/hooks/hooks.json          ← hook wiring (Session/Pre/Post/UserPrompt)
plugins/lensify/.claude-plugin/plugin.json
mcp_server/                               ← stdlib MCP stdio server (separate distribution)
tests/                                    ← 36 test files, 544 tests
.claude-plugin/{marketplace.json,plugin.json}  ← marketplace + root plugin manifest
docs/integrations/                        ← per-tool setup recipes (Cursor, VS Code, Codex…)
```

`pyproject.toml` maps the package alias `scripts` → `plugins/lensify/skills/lensify/scripts`
and exposes the CLI entry point `lensify = "scripts.scan:main"`. When editing source, edit
files under `plugins/lensify/skills/lensify/scripts/` — the top-level `skills/` dir is empty.

## Commands

```bash
# Run the full test suite (544 tests + 17 perf/security CI budgets)
pytest

# Run a single test file / test
pytest tests/test_capsule.py
pytest tests/test_capsule.py::test_name -v

# Perf + security budgets only (CI-enforced gate)
pytest tests/benchmark_perf.py

# Run the scan engine directly (this is what the skill shells out to)
python3 plugins/lensify/skills/lensify/scripts/scan.py <target-path> [--tier T1|T2|T3|auto] [--capsule-only] [--ast-only] [--no-git] [--output <dir>] [--install-agents-md [FILE]]

# Lifetime savings report
python3 plugins/lensify/skills/lensify/scripts/stats_cli.py

# Run the MCP server (for non-Claude hosts)
python3 -m mcp_server
```

Note: use `python3`, not `python` (macOS ships without a `python` binary — this was a real bug, see timeline).

## Architecture (the big picture)

**One engine, four distributions.** Adding a framework adapter benefits all four automatically.

| Channel | Hosts | Entry |
|---|---|---|
| Native plugin | Claude Code, Cowork | `hooks.json` + `SKILL.md` |
| MCP server | Cursor, VS Code Copilot, Codex, Gemini CLI, etc. | `mcp_server/` (hand-rolled JSON-RPC 2.0, no `pip install mcp`) |
| CLI | Aider, Copilot CLI, CI | `lensify <path>` |
| `AGENTS.md` context | any tool reading root context files | `scan.py --install-agents-md` |

**Scan pipeline** (`scan.py:scan()`): walk files (`walker.py`) → select complexity tier
T1/T2/T3 (`complexity.py`) → parse symbols (`ast_parser.py`, `symbols.py`) → run matched
framework adapters → analyze git hotspots (`git_analyzer.py`) → build capsule (`capsule.py`,
`section_matcher.py`) + HTML (`lens_html.py`) + optional LLM narrative (`narrative.py`,
`llm_client.py`). Outputs land in `lensify-out/`: `LENS.html`, `LENS.capsule.md`, `lens.json`,
`lens.sections.json`, `manifest.json` (hashes — used to skip rebuilds).

**Framework adapters** (`scripts/frameworks/`): a manifest-driven, lazy-loaded registry. Each
pack (`_ai_apps`, `_ai_uis`, `_ml_core`, `_serving`, `_vector_db`, `_experiment`, `_enterprise`,
`_notebooks`) subclasses `base.py:FrameworkAdapter`. `manifest.json` maps detection signals →
adapters so only matched adapters import. **30 adapters across 8 packs.** Add new ones by copying
`frameworks/_template/`. Shared helpers live in `frameworks/_util.py` (single copy, all packs import it).

**Hooks** (`hooks.json`, all under `scripts/`):
- `SessionStart` → `dedup_hook.py --session-start` + `memory_loader.py` (loads cross-session memory)
- `PreToolUse:Read` → `dedup_hook.py` (flags/blocks repeat reads of unchanged files)
- `PostToolUse:Edit|Write|NotebookEdit|Bash` → `activity_hook.py` (session activity tracking)
- `PostToolUse:Bash|WebFetch|…` → `compress_hook.py` (tool-output compression)
- `UserPromptSubmit` → `inject_hook.py` (selective capsule-section injection per prompt)

**State & telemetry:** session state in `session_state.py` + `.lensify-session.json`; cross-session
memory in `memory.py` (recency × module-overlap scoring, max 50); lifetime stats in `stats.py` →
`~/.lensify/stats.json`.

### Realized vs potential savings (important mental model)

A hook using only `additionalContext` can ADD tokens but never EVICT them, so it can only ever be a
**potential** saving. **Realized** savings require actually removing tokens from the model's input:
- `dedup_hook.py` with `LENSIFY_DEDUP_ENFORCE=1` → `permissionDecision: deny` blocks duplicate reads.
- `lensify run [--] <cmd>` wrapper (`scan.py:_run_wrapped`) compresses command output *before* it
  reaches the model; raw output is saved to `.lensify-outputs/`, exit code preserved, runs via
  list-args subprocess (no shell).
- `compress_hook.py` is opt-in (`LENSIFY_COMPRESS_OUTPUT=1`) because passive in-session compression is
  net-negative; its savings count only as potential.

`stats.py` splits the two: the headline number and `$ saved` are **realized only**; potential is shown
separately. When touching savings logic, preserve this honesty — do not report potential as realized.

## Conventions & constraints

- **Pure stdlib, no runtime deps.** `dependencies = []` in `pyproject.toml`. Don't add imports outside the stdlib in shipped engine/hook code.
- **Security budgets are CI-enforced** (`benchmark_perf.py`): no `exec`/`eval`/`pickle.loads`/`marshal.loads`/`shell=True`/`os.system`/`__import__` in shipped code; outbound HTTP confined to `llm_client.py` (Anthropic API only); user-defined adapters stay opt-in.
- **User adapters are opt-in** (`LENSIFY_USER_ADAPTERS=1`) — scanning a repo must never execute arbitrary code from it. Per-file read cap 1 MB (`LENSIFY_MAX_READ_BYTES`).
- **Confidence tags** (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`) must be preserved through capsule generation — never invent module names.
- **MCP stdout discipline:** the scan engine prints a JSON banner to stdout; the MCP server wraps every call in `redirect_stdout` so only JSON-RPC reaches the host. Don't add stray prints to stdout in engine code paths used by MCP.

### Environment variables

`LENSIFY_DEDUP`, `LENSIFY_DEDUP_ENFORCE`, `LENSIFY_COMPRESS_OUTPUT`, `LENSIFY_STATS`,
`LENSIFY_STATS_HOME`, `LENSIFY_USD_PER_MTOK`, `LENSIFY_MEMORY`, `LENSIFY_COMPACT_LLM`,
`LENSIFY_USER_ADAPTERS`, `LENSIFY_MAX_READ_BYTES`.

## Improvements timeline

Keep this updated as work lands. Full detail in `CHANGELOG.md`; this is the orientation summary.

| Version | Theme | Key change |
|---|---|---|
| (current branch `fix/honest-token-savings`) | **Honest token accounting** | dedup enforce-mode (`deny`), `lensify run` wrapper for realized savings, compress hook made opt-in, stats split realized vs potential. 544 tests. |
| v0.15.1 | Model-aware pricing + `python3` fix | stats price per active model (not always Opus); SKILL.md calls `python3`; inject hook hints when sections missing |
| v0.15.0 | Layered distribution | MCP server + CLI + `--install-agents-md` channels added; shared engine; MCP stdout-pollution fix |
| v0.14.1 | Security + governance | SECURITY.md, GOVERNANCE.md, 3 CI security tests; user adapters made opt-in (BREAKING); 1 MB read cap |
| v0.14.0 | `_enterprise` pack | SQLAlchemy/Pydantic/Vue/Tailwind/Docker Compose; adapter SDK template — 30 adapters / 8 packs |
| v0.13.0 | `_experiment` pack | W&B, MLflow, Comet |
| v0.12.0 | `_vector_db` pack | Pinecone, Weaviate, Qdrant, Chroma |
| v0.11.0 | `_serving` pack | vLLM, Triton, BentoML, Ray Serve |
| v0.10.0 | `_ai_uis` pack | Streamlit, Gradio, Chainlit |
| v0.9.0 | `_ml_core` pack | PyTorch, Transformers, scikit-learn, HF Datasets; shared `_util.py` hoisted |
| v0.8.0 | `_ai_apps` pack | LangChain, LlamaIndex, LangGraph, Pydantic AI, DSPy |
| v0.7.0 | Phase 9 — Adapter SDK | `FrameworkAdapter` base, manifest lazy-loading, `_notebooks` pack, perf harness |
| v0.1–0.6 | Phases 1–8 | dedup hook, session capsule, selective injection, conversation compactor, symbol snippets, output compression, cross-session memory, telemetry |

When you ship a notable change: add a `CHANGELOG.md` entry AND a row to this table (newest at top), bump the version in `pyproject.toml` + both `plugin.json` files, and update the test count if it changed.
