# Lensify

[![CI](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Version](https://img.shields.io/badge/version-0.15.0-brightgreen.svg)](CHANGELOG.md) [![Tests](https://img.shields.io/badge/tests-527%20passing-brightgreen.svg)](#tests--performance) [![Adapters](https://img.shields.io/badge/adapters-30%20across%208%20packs-blue.svg)](#framework-coverage)

> **Single-scan adaptive project lens + token-optimized context capsule for AI coding agents.** Cuts orientation tokens by 70–90%. Framework-aware across the full AI development lifecycle. Pure stdlib. MIT-licensed.

**📖 Read this in your language:** 🇨🇳 [简体中文](docs/i18n/README.zh-CN.md) · 🇹🇼 [繁體中文](docs/i18n/README.zh-TW.md) · 🇯🇵 [日本語](docs/i18n/README.ja.md) · 🇰🇷 [한국어](docs/i18n/README.ko.md) · 🇩🇪 [Deutsch](docs/i18n/README.de.md) · 🇫🇷 [Français](docs/i18n/README.fr.md) · 🇪🇸 [Español](docs/i18n/README.es.md) · 🇮🇳 [हिन्दी](docs/i18n/README.hi.md) · 🇧🇷 [Português](docs/i18n/README.pt.md) · 🇷🇺 [Русский](docs/i18n/README.ru.md) · 🇸🇦 [العربية](docs/i18n/README.ar.md) · 🇮🇹 [Italiano](docs/i18n/README.it.md) · 🇵🇱 [Polski](docs/i18n/README.pl.md) · 🇳🇱 [Nederlands](docs/i18n/README.nl.md) · 🇹🇷 [Türkçe](docs/i18n/README.tr.md) · 🇺🇦 [Українська](docs/i18n/README.uk.md) · 🇻🇳 [Tiếng Việt](docs/i18n/README.vi.md) · 🇮🇩 [Bahasa Indonesia](docs/i18n/README.id.md) · 🇸🇪 [Svenska](docs/i18n/README.sv.md) · 🇬🇷 [Ελληνικά](docs/i18n/README.el.md) · 🇷🇴 [Română](docs/i18n/README.ro.md) · 🇨🇿 [Čeština](docs/i18n/README.cs.md) · 🇫🇮 [Suomi](docs/i18n/README.fi.md) · 🇩🇰 [Dansk](docs/i18n/README.da.md) · 🇳🇴 [Norsk](docs/i18n/README.no.md) · 🇭🇺 [Magyar](docs/i18n/README.hu.md) · 🇹🇭 [ภาษาไทย](docs/i18n/README.th.md) · 🇺🇿 [O'zbekcha](docs/i18n/README.uz.md)

---

## Table of contents

1. [Why Lensify](#why-lensify)
2. [At a glance](#at-a-glance)
3. [Quick start](#quick-start)
4. [How it works](#how-it-works)
5. [Installation by tool (4 channels)](#installation-by-tool)
6. [Adaptive tiers — T1 / T2 / T3](#adaptive-tiers)
7. [Framework coverage — 30 adapters across 8 packs](#framework-coverage)
8. [Session hooks — 5 production hooks](#session-hooks)
9. [Conversation compactor](#conversation-compactor)
10. [Token economics — concrete numbers](#token-economics)
11. [Tests & performance budgets](#tests--performance)
12. [Security & governance](#security--governance)
13. [Configuration env vars](#configuration)
14. [Project structure](#project-structure)
15. [Extend it — write your own adapter](#extending-lensify)
16. [Comparison vs alternatives](#comparison)
17. [FAQ](#faq)
18. [Roadmap](#roadmap)
19. [Contributing & license](#contributing--license)

---

## Why Lensify

Modern AI coding agents have a context-window problem: the bigger the project, the more tokens they burn just **orienting themselves**. A typical onboarding flow reads 20–40 files before the agent can do useful work — that's 10–30k tokens spent on understanding, not solving the user's actual problem.

Lensify replaces that orientation phase with a **single scan** (sub-100 ms) that produces a token-bounded, framework-aware context block. The agent reads **one capsule** instead of dozens of files. Token usage drops 70–90% just from orientation savings — and the 5 session hooks stack additional savings on top.

**The trade-off it makes:** deterministic structural extraction (fast, free, framework-aware) instead of semantic vector search (slower, embedding cost, generic). Lensify works alongside semantic tools like Cursor's `@codebase` and Sourcegraph Cody — not against them. Use Lensify for instant orientation; reach for semantic search when the agent needs to find something specific by meaning rather than structure.

---

## At a glance

| Metric | Value |
|---|---|
| Framework adapters | **30** across 8 packs |
| Distribution channels | **4** (Plugin · MCP · CLI · AGENTS.md) |
| Session hooks (Claude Code) | **5** (dedup, activity, injection, compression, memory) |
| Tier budgets | T1 500 tok · T2 2,100 tok · T3 3,600 tok |
| Scan time (500 files) | **113 ms** |
| Hook subprocess startup | **< 250 ms** cold, ~30 ms warm |
| Plugin size | **203 KB** (Claude Code/Cowork bundle) |
| Runtime dependencies | **None** (pure Python stdlib) |
| Unit tests | **527 passing** |
| CI-enforced budgets | **17 performance + security** |
| License | MIT |
| Token savings | **70–90%** orientation · ~25% repeat-read · ~60% per-prompt re-injection · 8–25k per compaction |

---

## Quick start

Lensify has **three install paths**. Pick the one that matches your tool — every path takes under a minute.

### 👉 Claude Code (terminal) — one command in chat

```
/plugin marketplace add agenticailab01/lensify
/plugin install lensify@lensify
```

Then in any project: `/lensify` to scan, `/lensify compact` to recover tokens, `/lensify stats` for savings.

### 👉 Cowork (desktop app) — drag and drop

1. Download `lensify.plugin` from the [Releases page](https://github.com/agenticailab01/lensify/releases).
2. Drag the file into the Cowork chat window.
3. Click **Save plugin** on the preview card. Restart the conversation.

### 👉 Cursor / VS Code / Codex / Gemini CLI (MCP) — two transparent commands

Step 1 — clone the repo (one-time, ~200 KB):

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
```

Step 2 — register the MCP server. Pick the line that matches your tool:

```bash
# Cursor
cursor mcp add lensify python3 -m mcp_server --cwd ~/lensify

# VS Code
code --add-mcp '{"name":"lensify","type":"stdio","command":"python3","args":["-m","mcp_server"],"cwd":"'"$HOME"'/lensify"}'

# Claude Code MCP
claude mcp add lensify --scope user --cwd ~/lensify -- python3 -m mcp_server

# Gemini CLI
gemini mcp add lensify python3 -m mcp_server --cwd ~/lensify
```

These are your tool's **own** documented commands — no remote-script execution, no `curl | bash`. Three new tools appear after restart: `lensify_scan`, `lensify_compact`, `lensify_stats`.

Prefer a one-click button? See the install badges in [Installation by tool](#installation-by-tool).

📖 Full step-by-step instructions are in **[`USER-INSTALL.md`](USER-INSTALL.md)** — written for users who've never installed a plugin before.

Lensify auto-picks the tier (T1 Sketch / T2 Atlas / T3 Compass) based on project size and complexity. A 12-file script and a 4,000-file monorepo each get the right depth — the user reads **one page** either way.

---

## How it works

The scan engine runs five phases per invocation:

| Phase | What it does | Output |
|---|---|---|
| **1. Walk** | Respects `.gitignore` + vendor exclusions. Categorises every file as code / doc / meta. | File inventory |
| **2. Parse** | Python via stdlib `ast`. JS/TS/Go/Java via regex. Captures imports + public symbols. | Per-file metadata |
| **3. Tier** | Picks T1/T2/T3 from file count, LOC, top-level dirs, monorepo markers. | Token budget |
| **4. Adapt** | Lazy-loads matching framework adapters via manifest. Each emits a typed section. | Framework records |
| **5. Render** | Composes the capsule under tier budget. Writes HTML lens. Caches the result. | Capsule + HTML |

Typical runtime: **30 ms** on medium projects, **113 ms** on a 500-file project. The scan never re-reads files between phases.

**Two artefacts per scan:**

1. **`LENS.html`** — single self-contained HTML page (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns). For humans — 30-second read.
2. **`LENS.capsule.md`** — Markdown context block, 800–3,600 tokens, framework-aware. For your AI agent — ingested instead of reading 30+ raw files.

---

## Installation by tool

Four distribution channels share the same scan engine. Pick whichever matches your tool.

### Channel 1 — Claude Code / Cowork plugin (recommended)

The full experience: all 5 hooks fire, slash commands, statusline, memory loader.

**Claude Code (terminal CLI) — recommended:**

Type these two lines **inside the Claude Code chat** (not in your shell):

```
/plugin marketplace add agenticailab01/lensify
/plugin install lensify@lensify
```

The first line registers this GitHub repo as a plugin marketplace (it works because the repo has a `.claude-plugin/marketplace.json` file). The second installs the plugin from it. To uninstall later: `/plugin uninstall lensify@lensify`.

**Cowork (desktop chat):**
1. Download `lensify.plugin` from the [Releases page](https://github.com/agenticailab01/lensify/releases)
2. Drag-and-drop the file into the Cowork chat
3. Click **Save plugin** on the preview card
4. Restart the conversation — you'll see `Lensify dedup is active` confirming installation

After install, the plugin files land at:
- macOS: `~/.claude/plugins/lensify/`
- Linux: `~/.claude/plugins/lensify/`
- Windows: `%USERPROFILE%\.claude\plugins\lensify\`

> **Note:** the CLI does not support `claude plugin install <url>` — it works through the marketplace mechanism above. The two-line `/plugin marketplace add` + `/plugin install` flow is the supported path.

### Channel 2 — MCP server (Cursor, VS Code, Codex, Gemini CLI) — two transparent commands

**No `curl | bash`, no remote-script execution.** Each tool installs with two commands you type yourself: clone the repo, then run the tool's own MCP-add command. Every step is visible and reviewable.

#### Step 1 — clone the repo (one-time, ~200 KB, pure Python)

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
```

#### Step 2 — register the MCP server with your tool

Pick the line that matches your tool. **These are the tool's own commands** — they're documented, signed by the tool vendor, and accepted by any reasonable security policy.

| Tool | Command |
|---|---|
| **Cursor** | `cursor mcp add lensify python3 -m mcp_server --cwd ~/lensify` |
| **VS Code** | `code --add-mcp '{"name":"lensify","type":"stdio","command":"python3","args":["-m","mcp_server"],"cwd":"'"$HOME"'/lensify"}'` |
| **Claude Code MCP** | `claude mcp add lensify --scope user --cwd ~/lensify -- python3 -m mcp_server` |
| **Gemini CLI** | `gemini mcp add lensify python3 -m mcp_server --cwd ~/lensify` |
| **Codex** | append the `[mcp_servers.lensify]` block (below) to `~/.codex/config.toml` |

For Codex (no `mcp add` subcommand yet), append this block to `~/.codex/config.toml`:

```toml
[mcp_servers.lensify]
command = "python3"
args    = ["-m", "mcp_server"]
cwd     = "/Users/you/lensify"
```

Then fully restart the tool. Three new tools appear: `lensify_scan`, `lensify_compact`, `lensify_stats`.

#### 🖱️ Prefer a one-click button? (Cursor / VS Code)

These deeplinks open your editor's native MCP-install dialog and prompt you to confirm — no shell, no script, the tool itself handles the install:

[![Install in Cursor](https://img.shields.io/badge/Install%20in-Cursor-000000?style=for-the-badge&logo=cursor)](cursor://anysphere.cursor-deeplink/mcp/install?name=lensify&config=eyJjb21tYW5kIjogInB5dGhvbjMiLCAiYXJncyI6IFsiLW0iLCAibWNwX3NlcnZlciJdLCAiY3dkIjogIiRIT01FL2xlbnNpZnkifQ)
[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode)](vscode:mcp/install?%7B%22name%22%3A%22lensify%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22python3%22%2C%22args%22%3A%5B%22-m%22%2C%22mcp_server%22%5D%2C%22cwd%22%3A%22%24HOME%2Flensify%22%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/Install%20in-VS%20Code%20Insiders-24bfa5?style=for-the-badge&logo=visualstudiocode)](vscode-insiders:mcp/install?%7B%22name%22%3A%22lensify%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22python3%22%2C%22args%22%3A%5B%22-m%22%2C%22mcp_server%22%5D%2C%22cwd%22%3A%22%24HOME%2Flensify%22%7D)

You still need the repo cloned (Step 1 above). The buttons handle MCP registration, not the file checkout.

#### 📝 Manual config (when your tool isn't covered above)

Add this to the relevant MCP config file by hand:

```json
{
  "mcpServers": {
    "lensify": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/lensify"
    }
  }
}
```

Per-tool config file locations:

| Tool | Config file |
|---|---|
| Cursor | `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project) |
| VS Code Copilot Chat | `.vscode/mcp.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) |
| Gemini CLI | `~/.gemini/settings.json` |
| Codex | `~/.codex/config.toml` |

#### 🛡️ Why we don't use `curl | bash`

`bash <(curl -fsSL https://...)` is a classic supply-chain attack vector — the script is fetched and executed in one step, with no opportunity to review what it does. Modern AI assistants flag it, and security-conscious users (rightly) refuse it. We deliberately don't put it on the install page.

If you'd like a single command that does the clone + register in one go, the optional convenience scripts live in `install/` in this repo. Review the source first, then run locally:

```bash
# 1. Clone the repo
git clone https://github.com/agenticailab01/lensify ~/lensify
cd ~/lensify

# 2. Read what the script will do
cat install/install-cursor.sh        # ~20 lines, fully transparent

# 3. Run only if you're satisfied
bash install/install-cursor.sh
```

The scripts available: `install-cursor.sh`, `install-vscode.sh`, `install-claude-mcp.sh`, `install-gemini.sh`, `install-codex.sh`, `install-mcp.sh` (auto-detects multiple tools).

#### The 3 MCP tools

| Tool name | Arguments | What it does |
|---|---|---|
| `lensify_scan` | `path` (str, optional), `tier` ("T1"\|"T2"\|"T3"\|"auto"), `no_git` (bool) | Runs a full scan and returns the capsule + `LENS.html` path. |
| `lensify_compact` | `project_path` (str, optional), `llm` (bool) | Generates `WORKING_CONTEXT.md` from session state. |
| `lensify_stats` | (none) | Returns lifetime token-savings counters. |

#### How the MCP channel differs from the Plugin channel

| Capability | Plugin (Claude Code/Cowork) | MCP server (any tool) |
|---|:---:|:---:|
| `/lensify` scan | ✓ | ✓ (via `lensify_scan`) |
| `/lensify compact` | ✓ | ✓ (via `lensify_compact`) |
| `/lensify stats` | ✓ | ✓ (via `lensify_stats`) |
| 5 session hooks (dedup/inject/compress/memory/activity) | ✓ | ✗ (no hook surface in MCP spec) |

Scan/compact/stats are identical across both channels — same Python code under the hood. What you lose in MCP is the **passive** hook savings; what you gain is **broad tool support**.

#### Troubleshooting

| Symptom | Fix |
|---|---|
| Tool doesn't appear in picker | Verify `cwd` is the absolute path to your clone. Fully restart the tool. Check the tool's MCP logs (Cursor: View → Output → MCP). |
| `python3: command not found` | Edit the config to use the full path: `/usr/bin/python3` or `/opt/homebrew/bin/python3`. |
| Server starts but tools fail | Run `python3 -m mcp_server` manually from the `cwd`. If it errors there, fix that error first. |
| JSON-RPC parse errors | A stray `print()` is polluting stdout. Re-clone from a clean release tag. |
| Slow first call | Cold scan can take 100–250 ms on large repos. Subsequent calls are warm-cached. |

---

### Channel 3 — Standalone CLI (Aider, Copilot CLI, scripts, CI)

```bash
pip install lensify
lensify --version
lensify . --no-git
```

Available flags:
- `--tier T1|T2|T3|auto` — force a complexity tier (default: auto)
- `--capsule-only` — skip HTML, write only the Markdown capsule
- `--ast-only` — deterministic mode, no LLM enrichment of narrative
- `--no-git` — skip git hotspot analysis (faster)
- `--output <dir>` — override output directory (default: `<target>/lensify-out`)
- `--install-agents-md [FILE]` — append/update capsule inside a context file (default: `AGENTS.md`)
- `--version` — print version and exit

### Channel 4 — AGENTS.md write mode (any tool that reads context files)

```bash
lensify . --install-agents-md              # writes AGENTS.md
lensify . --install-agents-md CLAUDE.md
lensify . --install-agents-md GEMINI.md
lensify . --install-agents-md .cursorrules
```

The capsule lands inside the target file wrapped in idempotent `<!-- lensify-begin -->` / `<!-- lensify-end -->` markers. Re-running replaces only the marked block; any other content you've added is preserved.

---

## Adaptive tiers

Lensify picks the right depth automatically. Override with `--tier T1|T2|T3` only when you have a strong reason.

| Tier | Trigger | Capsule budget | Use case |
|---|---|---:|---|
| **T1 Sketch** | < 50 files · < 5k LOC · single language | 500 tok | Quick scripts, demos, single-file tools |
| **T2 Atlas** | 50–1,000 files · 5k–100k LOC · multi-module | 2,100 tok | Most real projects (the sweet spot) |
| **T3 Compass** | > 1,000 files · monorepo markers · 5+ top-level dirs | 3,600 tok | Monorepos, platforms, enterprise systems |

Override hints in chat — Lensify reads intent:

| Signal | Resulting tier |
|---|---|
| "quick summary" / "gist" / "tldr" | T1 |
| "onboard me" / "explain the project" / default | T2 |
| "monorepo" / "all services" / "full picture" | T3 |

---

## Framework coverage

30 adapters across 8 packs. Each adapter is ~80–120 LOC, lazy-loaded only when its framework signature matches the project.

### `_notebooks` — Exploration
| Adapter | What it surfaces |
|---|---|
| **Jupyter** | `.ipynb` structure: TOC headings, imports, defined functions/classes, execution status, cell counts |

### `_ml_core` — Modeling + training
| Adapter | What it surfaces |
|---|---|
| **PyTorch** | `nn.Module` subclasses, optimizers (Adam/SGD/AdamW), loss functions, DataLoaders, training-loop detection |
| **Transformers** | Auto* model loads with **checkpoint capture** (e.g. `distilbert-base-uncased`), tokenizers, pipeline tasks, Trainer + TrainingArguments |
| **scikit-learn** | Estimator instantiations (LogisticRegression, RandomForestClassifier, etc.), Pipeline, GridSearchCV, train_test_split, cross_val_score |
| **HF Datasets** | `load_dataset("name")` calls with **dataset name capture**, `.map`/`.filter` usage, DatasetDict |

### `_experiment` — Tracking + observability
| Adapter | What it surfaces |
|---|---|
| **Weights & Biases** | `wandb.init(project=, entity=, name=)`, Artifacts with type tags, sweeps + agents, watch calls |
| **MLflow** | `set_experiment`, `set_tracking_uri`, `start_run`, **model flavors** (sklearn/pytorch/tensorflow), log_param/metric/artifact counts |
| **Comet** | Experiment / OfflineExperiment / ExistingExperiment, project + workspace capture, log call counts |

### `_vector_db` — Embedding stores
| Adapter | What it surfaces |
|---|---|
| **Pinecone** | v2 + v3 clients, `Index("name")` references, `create_index` dimension + metric, upsert/query op counts |
| **Weaviate** | v3 + v4 clients, collection creates/gets, query primitives (near_vector/near_text/hybrid/bm25) |
| **Qdrant** | `QdrantClient`, `create_collection` with `VectorParams(size=, distance=)`, op counts |
| **Chroma** | All client variants (Persistent/Http/Ephemeral/Cloud), collection ops, embedding functions, op counts |

### `_ai_apps` — RAG + agentic
| Adapter | What it surfaces |
|---|---|
| **LangChain** | ChatPromptTemplate / PromptTemplate, LLMChain etc., LCEL pipe expressions (tagged INFERRED), agent constructors, `@tool` decorators |
| **LlamaIndex** | VectorStoreIndex / SummaryIndex / etc., query/chat/retriever engines, document readers, Settings assignments |
| **LangGraph** | `StateGraph` / `MessageGraph` topology — nodes + edges + entry/finish + conditional routes + checkpointer |
| **Pydantic AI** | `Agent(model)` constructors with model capture, `@agent.tool` / `tool_plain` / `system_prompt` / `result_validator` |
| **DSPy** | `Signature` subclasses, `Module` subclasses, `Predict`/`ChainOfThought`/`ReAct` predictors, optimizers, `settings.configure` |

### `_ai_uis` — LLM frontends
| Adapter | What it surfaces |
|---|---|
| **Streamlit** | Pages (via `set_page_config` / `pages/` dir / canonical names), widget mix, forms, cached fns, session_state usage |
| **Gradio** | `Interface` / `Blocks` / `ChatInterface` with title extraction, component counts, `.launch()` entry points |
| **Chainlit** | Lifecycle decorators (`@cl.on_message` / `on_chat_start` / `action_callback`), UI primitive counts (Message/Step/Action) |

### `_serving` — Production inference
| Adapter | What it surfaces |
|---|---|
| **vLLM** | `LLM(model=)` constructors with **checkpoint capture**, SamplingParams, async engines, OpenAI-compatible server entrypoints |
| **Triton (client)** | `InferenceServerClient` (http/grpc), InferInput/Output, **model names** from `.infer(model_name=)` calls |
| **BentoML** | `@bentoml.service` classes, `@bentoml.api/task/async_task` endpoints, Runners, IO schemas |
| **Ray Serve** | `@serve.deployment` + `@serve.ingress` (stacked decorators handled), `.bind()` bindings, `serve.run()` entrypoints |

### `_enterprise` — Full-stack backend
| Adapter | What it surfaces |
|---|---|
| **FastAPI** | Route decorators (GET/POST/PUT/DELETE/PATCH), path + method capture, `api_route(methods=[...])` expansion |
| **SQLAlchemy** | Declarative models, `__tablename__`, Column counts, `relationship()` declarations, `create_engine()` with **password redaction** |
| **Pydantic** | `BaseModel` / `RootModel` subclasses, field counts, `@field_validator` / `@model_validator`, `ConfigDict` flag |
| **Vue SFC** | `.vue` files; Composition API (`<script setup>`) vs Options API, `defineProps`/`defineEmits`/`defineExpose`, composables |
| **Tailwind** | `tailwind.config.{js,ts}` parsing — custom colors, fonts, theme.extend categories, plugins, content globs |
| **Docker Compose** | `docker-compose.yml` parsing (no PyYAML dep) — services, image/build, ports, volumes, **depends_on graph** |

A single Lensify scan on an AI-dev project surfaces every link in the chain: from raw notebooks through training, modeling, embeddings, agentic orchestration, UI components, and production deployments — all in **one capsule**, under budget.

---

## Session hooks

5 hooks compound across a Claude Code session. Token savings stack across the lifetime of the session.

| Hook | Event | Effect | Approximate savings |
|---|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file — agent gets a "you already saw this at turn N" hint | **~25%** on long sessions |
| `activity_hook.py` | PostToolUse:Edit \| Write \| Bash | Tracks session state; refreshes session capsule every 5 turns | Enables compactor |
| `inject_hook.py` | UserPromptSubmit | Injects only the **relevant** capsule sections per prompt (not the whole capsule) | **~60%** per-prompt savings |
| `compress_hook.py` | PostToolUse:Bash \| WebFetch | Deterministic compression of long tool outputs (HTML/JSON/log/trace/diff/pytest) | Variable, often 80%+ |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work | Carries context across `/clear` boundaries |

**Cowork limitation:** only SessionStart fires in Cowork's hook surface. The scan engine, capsule generation, and `/lensify compact` still work — but the 5 hook-driven optimizations only activate in Claude Code's terminal CLI.

---

## Conversation compactor

Long sessions eat context. The compactor reclaims 8–25k tokens in seconds.

```bash
/lensify compact          # generate WORKING_CONTEXT.md
/clear                        # flush the conversation buffer
# then paste WORKING_CONTEXT.md at the top of the new session
```

The compactor reads session state recorded by `activity_hook` and generates a `WORKING_CONTEXT.md` summarizing:

- Files you touched (with line counts and last operation)
- Bash commands run and their outcomes
- Tests that passed / failed
- Decisions made, open threads
- Optional LLM-enhanced one-paragraph summary if `ANTHROPIC_API_KEY` is set (one Haiku call, ~$0.001)

Empty state warning: if no PostToolUse hooks fired (typical in Cowork), the compactor outputs a clear diagnostic instead of pretending it captured work.

---

## Token economics

Where the savings come from — concrete numbers from production usage:

| Stage | Before Lensify | With Lensify | Savings |
|---|---|---|---:|
| Initial orientation | 8,000–20,000 tokens reading 20+ files | One capsule, 800–3,300 tokens | **70–90%** |
| Repeat reads | Each re-read costs full file (≈400 tok / 100 LOC) | Dedup flag, ~0 tokens | **~25%** on long sessions |
| Per-prompt re-injection | Full capsule (2,100 tok) every prompt | Only relevant sections (~800 tok) | **~60%** |
| Long tool outputs | Raw 50 KB Bash output → 12k tokens | Compressed summary + retrieval handle | **80%+** variable |
| Mid-session compaction | `/clear` loses everything | `WORKING_CONTEXT.md` preserves continuity | **8–25k** reclaimable |

**Cost example:** a 4-hour coding session that previously cost ~$3 (Opus) / ~$0.60 (Sonnet) in input tokens drops to ~$0.45–$0.90 / ~$0.09–$0.18 with all hooks active. `/lensify stats` auto-detects which model you're running and shows the correct rate.

---

## Tests & performance

**527 unit tests** + **17 CI-enforced performance + security budgets** run on every commit across macOS / Linux / Windows × Python 3.9–3.12.

Measured performance on synthetic project sizes:

| Project size | Files | Scan time | Capsule size | Sections rendered |
|---|---:|---:|---:|---:|
| Tiny | 20 | **41 ms** | 402 tok | 5 |
| Medium | 100 | **29 ms** | 529 tok | 5 |
| Large | 500 | **113 ms** | 529 tok | 5 |

Capsule size stays **bounded by tier budget regardless of project size** — linear scan time, constant output. That's the architectural moat.

Hard caps enforced in CI:

| Operation | Hard cap |
|---|---|
| Hook subprocess startup | < 250 ms |
| Scan on 100-file fixture | < 2.5 s |
| Capsule build | < 200 ms |
| Hook output envelope | ≤ 500 tokens per event |
| `SKILL.md` size | < 8 KB |
| Rule R1 — hooks framework-free | static-analysis enforced |
| Rule R3 — `detect()` never opens files | static-analysis enforced |

Adding adapters can't regress any of these. Pull requests that violate a budget fail CI.

---

## Security & governance

Lensify is the most security-hardened tool in its category. See [`SECURITY.md`](SECURITY.md) for the full threat model.

**CI-enforced safety:**
- `exec()`, `eval()`, `__import__()`, `pickle.loads()`, `marshal.loads()`, `shell=True`, `os.system()` are **statically banned** in shipped code
- Outbound HTTP confined to a single allowlisted endpoint (`api.anthropic.com`) inside `llm_client.py`
- User-defined adapter loader is **opt-in** via `LENSIFY_USER_ADAPTERS=1` (off by default — scanning a malicious repo cannot execute arbitrary Python without explicit user opt-in)
- 1 MB per-file read cap prevents DoS via huge files
- 30-second `git` subprocess timeout

**What's persisted locally:**

| Data | Location | Lifetime | Opt-out |
|---|---|---|---|
| Lifetime stats counters | `~/.lensify/stats.json` | Permanent | `LENSIFY_STATS=0` |
| Cross-session memory | `<project>/.lensify-memory/*.json` | Per-project, max 50 (LRU) | `LENSIFY_MEMORY=0` |
| Session state | `<project>/lensify-out/state.json` | Per-session | `LENSIFY_DEDUP=0` |
| Capsule + lens artefacts | `<project>/lensify-out/` | Regenerated each scan | n/a |

**Nothing is sent off-device** unless you explicitly run `/lensify compact --llm`. Stats and memory files are plain JSON — auditable, deletable, no PII.

For governance — what contributions we accept and what we don't — see [`GOVERNANCE.md`](GOVERNANCE.md).

---

## Configuration

All persistent surfaces have documented env var opt-outs:

```bash
# Hook control
export LENSIFY_DEDUP=0              # disable ALL hooks (dedup/activity/inject/compress/memory)
export LENSIFY_COMPRESS_OUTPUT=0    # disable just output compression

# Persistence control
export LENSIFY_STATS=0              # disable lifetime stats counters
export LENSIFY_STATS_HOME=/path     # change where stats live (default ~/.lensify)
export LENSIFY_MEMORY=0             # disable cross-session memory

# Resource limits
export LENSIFY_MAX_READ_BYTES=N     # per-file read cap in bytes (default 1MB)

# Trust gating (opt-in only)
export LENSIFY_USER_ADAPTERS=1      # opt IN to user-defined adapters from <project>/.lensify/frameworks/

# Optional LLM enhancement
export ANTHROPIC_API_KEY=sk-...         # enables /lensify compact --llm narrative
```

Unset to re-enable. Nothing else changes — no plugin files moved, no data lost.

---

## Project structure

```
lensify/
├── .claude-plugin/
│   └── plugin.json                     # Cowork / Claude Code manifest
├── .github/
│   ├── workflows/ci.yml                # GitHub Actions: tests + perf budgets
│   ├── ISSUE_TEMPLATE/                 # bug / adapter request / feature templates
│   └── PULL_REQUEST_TEMPLATE.md
├── hooks/
│   └── hooks.json                      # SessionStart + 4 PostToolUse hook registrations
├── mcp_server/
│   ├── __init__.py
│   ├── __main__.py                     # python -m mcp_server entry
│   └── server.py                       # pure-stdlib JSON-RPC 2.0 stdio implementation
├── skills/lensify/
│   ├── SKILL.md                        # Skill definition (lean — under 8KB)
│   ├── references/                     # 13 deep-dive reference docs (lazy-loaded)
│   │   ├── adapter-sdk.md              # Contributor guide
│   │   ├── capsule-format.md
│   │   ├── conversation-compactor.md
│   │   ├── cross-session-memory.md
│   │   ├── dedup-hook.md
│   │   ├── output-compression.md
│   │   ├── selective-injection.md
│   │   ├── session-capsule.md
│   │   ├── symbol-snippets.md
│   │   ├── telemetry.md
│   │   ├── complexity-tiers.md
│   │   ├── diagram-selection.md
│   │   └── narrative-prompts.md
│   └── scripts/
│       ├── scan.py                     # Main entry point — the scan engine
│       ├── walker.py                   # Filesystem walker, .gitignore-aware
│       ├── ast_parser.py               # AST + regex parsing
│       ├── complexity.py               # Tier detection + token budgets
│       ├── capsule.py                  # Capsule composer
│       ├── compact.py                  # Conversation compactor
│       ├── llm_client.py               # Optional Anthropic API (single allowlisted endpoint)
│       ├── session_state.py            # Per-session activity tracking
│       ├── memory.py                   # Cross-session memory store
│       ├── stats.py                    # Lifetime stats + statusline
│       ├── output_compressor.py        # 9 deterministic compressors
│       ├── symbols.py                  # Public symbol ranker
│       ├── git_analyzer.py             # Git hotspot detection
│       ├── section_matcher.py          # Per-prompt section relevance
│       ├── narrative.py                # LENS.html narrative panel
│       ├── frameworks/                 # 30 adapters across 8 packs
│       │   ├── base.py                 # FrameworkAdapter SDK contract
│       │   ├── registry.py             # Manifest-driven lazy loading
│       │   ├── manifest.json           # 30 entries — sig → module
│       │   ├── _util.py                # Shared file-read helper
│       │   ├── _template/              # SDK starter (copy to begin)
│       │   ├── _ai_apps/               # LangChain, LlamaIndex, LangGraph, Pydantic AI, DSPy
│       │   ├── _ai_uis/                # Streamlit, Gradio, Chainlit
│       │   ├── _ml_core/               # PyTorch, Transformers, sklearn, Datasets
│       │   ├── _serving/               # vLLM, Triton, BentoML, Ray Serve
│       │   ├── _vector_db/             # Pinecone, Weaviate, Qdrant, Chroma
│       │   ├── _experiment/            # W&B, MLflow, Comet
│       │   ├── _enterprise/            # FastAPI, SQLAlchemy, Pydantic, Vue, Tailwind, Compose
│       │   └── _notebooks/             # Jupyter parser + adapter
│       ├── dedup_hook.py               # PreToolUse:Read
│       ├── activity_hook.py            # PostToolUse:Edit|Write|Bash
│       ├── inject_hook.py              # UserPromptSubmit
│       ├── compress_hook.py            # PostToolUse:Bash|WebFetch
│       ├── memory_loader.py            # SessionStart
│       └── statusline.py               # Token-usage statusline
├── tests/                              # 527 unit tests + 17 perf/security budgets
├── docs/
│   ├── i18n/                           # 29 translated READMEs
│   ├── integrations/                   # Per-tool recipes (Cursor, VS Code, Codex, etc.)
│   └── screenshots/                    # Visual mockups
├── pyproject.toml                      # CLI entry point + Python metadata
├── README.md                           # This file
├── CHANGELOG.md                        # v0.1 → v0.15 release notes
├── CONTRIBUTING.md                     # How to contribute
├── CODE_OF_CONDUCT.md
├── SECURITY.md                         # Threat model + vulnerability reporting
├── GOVERNANCE.md                       # Scope of project + abuse mitigations
├── BENCHMARK.md                        # Competitive matrix + measured numbers
├── LICENSE                             # MIT
└── .gitignore
```

---

## Extending Lensify

The adapter SDK is intentionally small. Each adapter is ~80–120 LOC.

### Write a new framework adapter

```bash
cd skills/lensify/scripts/frameworks
cp -r _template _myframework
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes
$EDITOR manifest.json                    # register entry
$EDITOR ../../../../tests/test_myframework.py   # add tests
```

The contract every adapter must follow:

| Rule | What |
|---|---|
| **R1** | Hook scripts never import from `frameworks/*` (CI-enforced) |
| **R2** | Adapter modules stay small — ~80–120 LOC |
| **R3** | `detect()` is O(1) — never opens files (CI-enforced) |
| **R4** | `extract()` reads only files that match your framework's signature |
| **R5** | `capsule_section()` respects `budget_tokens` |

Full guide: [`skills/lensify/references/adapter-sdk.md`](skills/lensify/references/adapter-sdk.md).

### Per-project user adapters (no fork needed)

Drop `.py` files into `<your-project>/.lensify/frameworks/`. They're auto-discovered per scan once you opt in:

```bash
export LENSIFY_USER_ADAPTERS=1
```

The trust decision happens in your shell, not in the code being scanned — protecting you from malicious adapters in untrusted repos.

---

## Comparison

Lensify is **the lightweight, deterministic orientation layer** in the AI coding assistant space. It complements semantic-search tools rather than replacing them.

| Capability | Repomix | Aider repo-map | Cursor `@codebase` | Sourcegraph Cody | Graphify | Caveman | **Lensify** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Single-pass summary | ✓ | ✓ | ✓ (search) | ✓ (search) | ✓ | ✓ | **✓** |
| Token-bounded output | ~ | ~ | ✗ | ✗ | ✗ | ~ | **✓ tier-locked** |
| Adaptive depth (auto-tier) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ T1/T2/T3** |
| Framework-aware extraction | ✗ | ✗ | ~ | ~ | ✗ | ~ | **✓ 30 adapters** |
| Confidence tags on output | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ EXTRACTED/INFERRED/AMBIGUOUS** |
| In-session hooks | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ 5 hooks** |
| Mid-session compaction | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ /lensify compact** |
| Multi-tool support | CLI | Aider | Cursor | Cody | CLI | CLI | **✓ 4 channels** |
| Plugin size | ~80KB | bundled | bundled | hosted | n/a | ~10KB | **203 KB** |
| Runtime deps | none | aider | Cursor | account | none | minimal | **stdlib only** |
| CI-enforced security audit | ✗ | ✗ | hosted | hosted | ✗ | ✗ | **✓ 3 static checks** |
| Open source | ✓ | ✓ | ✗ | ~ | ✓ | ✓ | **✓ MIT** |
| Semantic / vector search | ✗ | ~ | ✓ | ✓ | ✗ | ✗ | **✗** (out of scope) |

See [`BENCHMARK.md`](BENCHMARK.md) for the full competitive analysis.

---

## FAQ

**Q: Does it work on my JS/TS / Go / Rust project?**
A: The base scan (file walk, language detection, symbols) works on JS, TS, Go, Java, Rust, Ruby, PHP, C/C++, and ~20 other languages. The 30 framework-specific adapters are mostly Python-focused right now, with Vue SFC + Tailwind + Docker Compose covering the JS/web side. JS/TS framework adapters (Next.js, Astro, SvelteKit, NestJS) are on the roadmap.

**Q: Will it slow down my Claude Code session?**
A: Hook subprocess startup is capped at 250 ms cold (typically 20–30 ms warm). Hook output is capped at 500 tokens per event. Both caps are CI-enforced. The scan itself runs on-demand, not per-prompt.

**Q: Does it send my code anywhere?**
A: No, unless you explicitly run `/lensify compact --llm` AND have `ANTHROPIC_API_KEY` set. Even then, only the session activity summary (file paths, command names, test results) is sent — never file contents.

**Q: Is the capsule different from a README?**
A: A README tells **humans** what the project does. The capsule tells your **agent** what the project contains: routes, models, training loops, vector indexes, deployments, etc. Different audience, different output, both have their place.

**Q: What if my framework isn't covered by an adapter?**
A: The base scan still produces a useful capsule (entry points, modules, symbols, hotspots, risks). You get less framework-specific noise. Add a custom adapter in ~100 LOC if you want richer output for that framework — see [the adapter SDK guide](skills/lensify/references/adapter-sdk.md).

**Q: Can I disable everything and just use the scan?**
A: Yes — `export LENSIFY_DEDUP=0` disables all 5 hooks. The scan engine remains available for explicit `/lensify` invocations.

**Q: Why not use Cursor's @codebase or Sourcegraph Cody instead?**
A: They do **semantic** vector search — they need an embedding model, a vector store, and continuous indexing. Lensify does **structural** extraction — deterministic, fast (sub-second), cheap, and framework-aware. The two are complementary: Lensify for instant orientation, semantic tools for in-depth search.

**Q: How does compaction interact with `/clear`?**
A: Run `/lensify compact` first (generates `WORKING_CONTEXT.md`), then `/clear` to flush the conversation buffer, then paste the contents of `WORKING_CONTEXT.md` at the top of the next session. You resume with the same shoulder-context but a fresh token budget. Compaction typically reclaims 8–25k tokens.

**Q: Is it free?**
A: Yes — MIT licensed. No subscription, no telemetry sent off-device, no required pip dependencies.

**Q: How do I update to the latest version?**
A: Depends on your install path. **Claude Code plugin:** run `/plugin uninstall lensify@lensify` then `/plugin install lensify@lensify` inside chat — this refreshes the local cache. **Cowork:** re-download `lensify.plugin` from the Releases page and drag it in again. **MCP / git clone:** `cd ~/lensify && git pull`, then restart your tool. **pip CLI:** `pip install --upgrade lensify`. Full step-by-step in [`USER-INSTALL.md`](USER-INSTALL.md#updating-to-the-latest-version).

**Q: How do I uninstall?**
A: Claude Code CLI: `/plugin uninstall lensify@lensify` then `/plugin marketplace remove agenticailab01/lensify`. Cowork: settings → Plugins → Lensify → Remove. MCP users: delete the `lensify` entry from your MCP config and `rm -rf ~/lensify`. Pip CLI users: `pip uninstall lensify`. To wipe persisted data: `rm -rf ~/.claude/plugins/lensify ~/.lensify` and `<project>/.lensify-memory`.

---

## Roadmap

| Pack | Status | Notes |
|---|---|---|
| `_ai_apps` v2 — LiteLLM, Instructor, AutoGen | Planned | Next AI-dev sprint |
| `_ml_core` v2 — JAX, Flax, MLX, fastai | Planned | After v2 ai_apps |
| `_serving` v2 — Modal, Replicate, Cog | Planned | |
| `_enterprise` v2 — Django, Flask, Next.js, NestJS | Planned | JS/TS framework coverage |
| Multi-modal lightweight — SQL schemas, shell scripts, Dockerfile, Markdown docs | Investigating | v0.16.0 candidate |
| Optional graph mode — `lensify graph .` + MCP graph queries | Investigating | v0.17.0 candidate |
| `lensify watch` daemon — auto-refresh AGENTS.md on file changes | Investigating | Cross-tool freshness |

Vote with GitHub issues — what should come first?

---

## Contributing & license

We welcome:
- New framework adapters (see [`CONTRIBUTING.md`](CONTRIBUTING.md))
- Bug fixes with regression tests
- Doc improvements + new integration recipes
- Performance work that keeps the perf budgets green

We don't accept:
- `exec`, `eval`, `pickle.loads`, `shell=True`, `os.system` (CI-enforced)
- New outbound HTTP endpoints
- Telemetry or analytics sent off-device
- Adapters with hardcoded credentials or scraping behavior

See [`GOVERNANCE.md`](GOVERNANCE.md) for the full policy.

**License:** MIT. © Sachin Patil. See [`LICENSE`](LICENSE).

**Maintainer:** Sachin Patil — `agenticailab01@gmail.com`. For security reports, see [`SECURITY.md`](SECURITY.md).

---

⭐ Star this repo if Lensify saves you tokens. Open an issue if a framework you use isn't covered — most adapters are ~100 LOC and we'll prioritize.
