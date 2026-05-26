# Changelog

All notable changes to Lensify.

## v0.15.0 — Layered distribution (MCP + CLI + AGENTS.md)

Lensify now ships in **four distribution channels** so it works with virtually any AI coding tool. The Claude Code / Cowork plugin stays exactly as-is — the three new channels are *additive*, reuse the same scan engine, and add zero dependencies to plugin users.

### Added
- **`mcp_server/`** — pure-stdlib MCP stdio server (JSON-RPC 2.0, ~250 LOC). Exposes three tools: `lensify_scan`, `lensify_compact`, `lensify_stats`. Compatible with Cursor, VS Code Copilot Chat, Codex, Gemini CLI, OpenCode, Trae, Kiro, Antigravity, and any other MCP host. No `pip install mcp` required — the protocol is hand-rolled stdlib-only.
- **`--install-agents-md` flag** on `scan.py` — writes the capsule into `AGENTS.md` (or any custom path: `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, etc.) using the idempotent `<!-- lensify-begin -->` / `<!-- lensify-end -->` markers. Any tool that reads project-root context files gets the capsule for free.
- **CLI entry point** finalised — `pyproject.toml` already exposed `lensify = "scripts.scan:main"`; works once published to PyPI.
- **`docs/integrations/`** — per-tool recipes for Cursor, VS Code Copilot Chat, Codex, Gemini CLI, Aider, generic MCP, and AGENTS.md mode.
- **11 new tests** in `test_layered_distribution.py` covering CLI invocation, AGENTS.md install + idempotency + custom paths, MCP initialize/tools/list/tools/call/error-handling/notification-ignore/malformed-input.

### Fixed
- **MCP stdout pollution bug** — the scan engine prints a JSON banner to stdout. In an MCP stdio context that would corrupt the JSON-RPC stream. The MCP server now wraps every tool call in `contextlib.redirect_stdout(StringIO())` so engine output is captured and discarded; only well-formed JSON-RPC reaches the host's stdin.

### Architecture
The four channels share one engine — adding a framework adapter benefits all four distributions automatically. See `docs/integrations/README.md` for the channel-routing strategy.

| Channel | Tools | Setup |
|---|---|---|
| Native plugin | Claude Code, Cowork | Drop in `lensify.plugin` |
| MCP server | Cursor, VS Code Copilot Chat, Codex, Gemini CLI, OpenCode, Trae, Kiro, Antigravity | `python -m mcp_server` in MCP config |
| CLI | Aider, GitHub Copilot CLI, scripts, CI | `pip install lensify && lensify <path>` |
| `AGENTS.md` context | Any tool that auto-reads project context | `lensify . --install-agents-md` |

### Stats
- 527 unit tests pass (was 516; +11 for layered distribution)
- 17 perf/security budgets pass (unchanged)
- Plugin size unchanged (201 KB) — MCP server is a separate distribution

---

## v0.14.1 — Security + governance hardening

### Added
- **`SECURITY.md`** — threat model, audit results, outbound-network policy, data-handling table, vulnerability reporting process
- **`GOVERNANCE.md`** — scope of use, acceptable / unacceptable contributions, anti-spam + anti-abuse mitigations, user-rights, license
- **3 CI-enforced security tests** in the perf harness:
  - `test_no_forbidden_security_patterns` — bans `exec` / `eval` / `pickle.loads` / `marshal.loads` / `shell=True` / `os.system` / `__import__` in shipped code
  - `test_outbound_network_only_anthropic_api` — confines outbound HTTP to `llm_client.py`
  - `test_user_adapter_loader_is_opt_in` — proves the user-adapter loader stays gated

### Changed (BREAKING for power users)
- **User-defined adapters are now opt-in.** Previously `<project>/.lensify/frameworks/*.py` was auto-loaded per scan — meaning scanning a malicious repo could execute arbitrary Python in the agent's environment. Now off by default; set `LENSIFY_USER_ADAPTERS=1` in your shell rc to enable.
- **Per-file read cap of 1 MB** for all framework adapter file reads (configurable via `LENSIFY_MAX_READ_BYTES`). Prevents resource-exhaustion DoS from huge generated/vendored files.

### Stats
- 17 perf/security budgets pass (was 14)
- 516 unit tests pass

---

## v0.14.0

### Added
- **`_enterprise` pack expansion** — 5 new adapters: SQLAlchemy (models + tables + relationships + engine URL with password redaction), Pydantic (BaseModel + fields + validators + ConfigDict), Vue SFC (`.vue` files; props + emits + composables + setup vs Options API), Tailwind (config customisations: theme.extend colors/fonts, plugins, content globs), Docker Compose (services + ports + volumes + depends_on graph)
- **Adapter SDK template** — `frameworks/_template/` directory with a fully-annotated reference adapter for community contributors. Copy + edit; the SDK README explains every contract requirement
- **Production README + CHANGELOG** — top-level docs covering install, usage, full adapter list, token economics, performance budgets, project structure
- **Registry signal expansion** — `_collect_signals()` now recognises multi-dot config filenames (`tailwind.config.js` → `tailwind`) and Docker Compose files (`docker-compose.yml` → `docker-compose`)

### Stats
- 30 framework adapters across 8 packs
- 515 unit tests + 14 perf budgets pass

---

## v0.13.0

### Added
- **`_experiment` pack** — Weights & Biases (project/entity capture, artifacts, sweeps), MLflow (experiments, runs, model flavors: sklearn/pytorch/tensorflow/transformers/langchain), Comet (online/offline/existing experiments, log_metric/parameter/asset)

### Stats
- 25 adapters across 8 packs
- 490 tests pass

---

## v0.12.0

### Added
- **`_vector_db` pack** — Pinecone (v2 + v3 APIs, index dimensions/metric, op counts), Weaviate (connect_to_local/wcs, collections, query primitives), Qdrant (QdrantClient, vectors_config size/distance, ops), Chroma (all client variants, collections, embedding functions, ops)

### Fixed
- Pinecone + Qdrant: regex bug where `[^)]*?` non-greedy combined with optional groups silently collapsed `dimension`/`size` kwargs to zero-width. Refactored to two-step pattern (capture args block → run separate regexes per kwarg)

### Stats
- 22 adapters across 7 packs
- 475 tests pass

---

## v0.11.0

### Added
- **`_serving` pack** — vLLM (LLM model checkpoint capture, SamplingParams, OpenAI server entry), Triton (InferenceServerClient HTTP+gRPC, InferInput/Output, model references), BentoML (services, APIs, runners, IO schemas), Ray Serve (deployments, ingress with stacked decorators, bindings, serve.run)

### Notable
- Ray Serve uses broad `import ray` signature but filters out non-Serve files in `extract()` — Ray Train/Tune/Data projects don't emit spurious sections

### Stats
- 18 adapters across 6 packs
- 455 tests pass

---

## v0.10.0

### Added
- **`_ai_uis` pack** — Streamlit (pages via `set_page_config` + `pages/` dir + canonical roots, widget mix, forms, cached funcs, session_state), Gradio (Interface/Blocks/ChatInterface with title extraction, component counts, `.launch()` entrypoints), Chainlit (lifecycle decorators, UI primitives)

### Stats
- 14 adapters across 5 packs
- 434 tests pass

---

## v0.9.0

### Added
- **`_ml_core` pack** — PyTorch (nn.Module subclasses, optimizers, losses, DataLoader, training-loop detection), Transformers (Auto* model loads with checkpoint capture, AutoTokenizer, pipeline, Trainer + TrainingArguments), scikit-learn (estimator whitelist, Pipeline, GridSearchCV, train_test_split, cross_val_score), HF Datasets (load_dataset with name capture, .map/.filter)
- **Framework budget bump** — T2 frameworks 200→400 tok (total 1900→2100), T3 frameworks 400→700 (total 3300→3600) to accommodate more packs
- **Shared `_util.py` hoisted to `frameworks/_util.py`** — every pack imports from one copy instead of duplicating

### Fixed
- `compact.py` version string was stuck at v0.3.0
- `compact.py` empty-state: explicit warning when no PostToolUse hooks fired (typical in Cowork) — points users to Claude Code for full compaction
- Transformers double-match: `AutoTokenizer` was being matched as both model and tokenizer (regex `Auto\w+` was too broad)

### Stats
- 11 adapters across 4 packs
- 419 tests pass

---

## v0.8.0

### Added
- **`_ai_apps` pack** — LangChain (prompts, chains, agents, tools, LCEL pipes tagged INFERRED), LlamaIndex (indexes, query/chat engines, readers, Settings), LangGraph (StateGraph + node/edge graph topology, checkpointers), Pydantic AI (Agent + tools + system_prompt + result_validator), DSPy (Signature, Module, ChainOfThought, optimizers)

### Stats
- 7 adapters across 4 packs
- 399 tests pass

---

## v0.7.0

### Added
- **Phase 9 — Framework Adapter SDK**
  - `FrameworkAdapter` base class + `FrameworkInfo`/`FrameworkEntry` records
  - Manifest-driven lazy loading (only matched adapters import)
  - User-extensible slot at `<project>/.lensify/frameworks/`
  - Reference adapter: FastAPI
- **`_notebooks` pack** — Jupyter (`.ipynb` parsing without external deps: TOC, imports, defines, executed/not-run status, cell counts)
- **Performance harness** — 14 enforced perf budgets covering hook startup, scan time, capsule build, R1 (hooks framework-free), R3 (detect never opens files), SKILL.md size, locked tier budgets

---

## v0.6.0

### Added
- **Phase 8 — Statusline + Telemetry** — lifetime stats JSON at `~/.lensify/stats.json`, statusline command, CLI tool

---

## v0.5.0

### Added
- **Phase 6 — Output compression** — 9 deterministic compressors (HTML, JSON, log, trace, diff, Playwright, pytest, tabular, text fallback) hooked into PostToolUse
- **Phase 7 — Cross-session memory** — persistent memory with recency × module-overlap scoring (max 50 memories)

---

## v0.4.0

### Added
- **Phase 5 — Symbol micro-snippets** — `SYMBOLS` section in capsule with ranked public signatures (Python ast, JS/TS regex, Go regex)

---

## v0.3.0

### Added
- **Phase 4 — Conversation compactor** — `/lensify compact` generates `WORKING_CONTEXT.md` to reclaim 8-25k tokens via `/clear` with continuity. Stdlib-only Anthropic API client for optional LLM-enhanced summaries

---

## v0.2.0

### Added
- **Phase 2 — Session capsule** — activity tracking + capsule refresh every 5 turns
- **Phase 3 — Selective injection** — UserPromptSubmit hook injects only the relevant capsule sections per prompt (~60% token savings on per-prompt re-injection)

---

## v0.1.1

### Added
- **Phase 1 — Read dedup hook** — PreToolUse:Read flags repeated reads of the same file

---

## v0.1.0

### Initial release
- One-page adaptive project lens (T1 Sketch / T2 Atlas / T3 Compass)
- Token-optimized context capsule with per-tier token budgets
- HTML one-pager + Markdown capsule
- Heuristic shape detection (layered / hub-spoke / pipeline / domain-map)
- Confidence-tagged risks
