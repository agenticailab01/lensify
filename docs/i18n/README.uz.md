# Lensify

> 🌐 **O'zbekcha** — Inglizchaga qaytish: [English](../../README.md)


[![CI](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE) [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Version](https://img.shields.io/badge/version-0.15.0-brightgreen.svg)](../../CHANGELOG.md) [![Tests](https://img.shields.io/badge/tests-527%20passing-brightgreen.svg)](#tests--performance) [![Adapters](https://img.shields.io/badge/adapters-30%20across%208%20packs-blue.svg)](#framework-coverage)

> **AI kodlash agentlari uchun bir martalik skanerlash adaptiv loyiha linzasi + token uchun optimallashtirilgan kontekst kapsulasi.** Yo'naltirish tokenlarini 70–90% ga kamaytiradi. AI ishlab chiqish hayot aylanishi davomida framework xabardorligi. Toza standart kutubxona. MIT litsenziyasi.

**📖 O'z tilingizda o'qing:** 🇬🇧 [← Inglizchaga qaytish](../../README.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇹🇼 [繁體中文](README.zh-TW.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇩🇪 [Deutsch](README.de.md) · 🇫🇷 [Français](README.fr.md) · 🇪🇸 [Español](README.es.md) · 🇮🇳 [हिन्दी](README.hi.md) · 🇧🇷 [Português](README.pt.md) · 🇷🇺 [Русский](README.ru.md) · 🇸🇦 [العربية](README.ar.md) · 🇮🇹 [Italiano](README.it.md) · 🇵🇱 [Polski](README.pl.md) · 🇳🇱 [Nederlands](README.nl.md) · 🇹🇷 [Türkçe](README.tr.md) · 🇺🇦 [Українська](README.uk.md) · 🇻🇳 [Tiếng Việt](README.vi.md) · 🇮🇩 [Bahasa Indonesia](README.id.md) · 🇸🇪 [Svenska](README.sv.md) · 🇬🇷 [Ελληνικά](README.el.md) · 🇷🇴 [Română](README.ro.md) · 🇨🇿 [Čeština](README.cs.md) · 🇫🇮 [Suomi](README.fi.md) · 🇩🇰 [Dansk](README.da.md) · 🇳🇴 [Norsk](README.no.md) · 🇭🇺 [Magyar](README.hu.md) · 🇹🇭 [ภาษาไทย](README.th.md)

---

## Mundarija

1. [Nima uchun Lensify](#why-lensify)
2. [Bir qarashda](#at-a-glance)
3. [Tezkor boshlash](#quick-start)
4. [Qanday ishlaydi](#how-it-works)
5. [Vositaga ko'ra o'rnatish (4 kanal)](#installation-by-tool)
6. [Moslashuvchan darajalar — T1 / T2 / T3](#adaptive-tiers)
7. [Framework qamrovi — 8 paketdagi 30 adapter](#framework-coverage)
8. [Sessiya hooklari — 5 ishlab chiqarish hooki](#session-hooks)
9. [Suhbat siqishtirgich](#conversation-compactor)
10. [Token iqtisodiyoti — aniq raqamlar](#token-economics)
11. [Testlar va samaradorlik byudjetlari](#tests--performance)
12. [Xavfsizlik va boshqaruv](#security--governance)
13. [Konfiguratsiya muhit o'zgaruvchilari](#configuration)
14. [Loyiha tuzilishi](#project-structure)
15. [Kengaytiring — o'z adapteringizni yozing](#extending-lensify)
16. [Muqobillar bilan taqqoslash](#comparison)
17. [FAQ](#faq)
18. [Yo'l xaritasi](#roadmap)
19. [Hissa qo'shish va litsenziya](#contributing--license)

---

## Nima uchun Lensify

Zamonaviy AI kodlash agentlari kontekst oynasi muammosiga ega: loyiha qanchalik katta bo'lsa, ular faqat **o'zlarini yo'naltirish** uchun shunchalik ko'p tokenlarni yoqadi. Tipik onboarding oqimi agentga foydali ish qila olishidan oldin 20-40 fayl o'qiydi — bu foydalanuvchining haqiqiy muammosini hal qilishga emas, balki tushunishga sarflanadigan 10-30k token degani.

Lensify bu yo'naltirish bosqichini **bitta skanerlash** (100 ms dan kam) bilan almashtiradi, bu token bilan chegaralangan, framework xabardor kontekst bloki ishlab chiqaradi. Agent o'nlab fayllar o'rniga **bitta kapsula** o'qiydi. Token foydalanish faqat yo'naltirish tejamlaridan 70-90% kamayadi.

**Murosa:** semantik vektor qidiruvi o'rniga deterministik tizimli ekstraksiya. Lensify semantik vositalar bilan birga ishlaydi, ularga qarshi emas.

---

## Bir qarashda

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

## Tezkor boshlash

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

### 👉 Cursor / VS Code / Codex / Gemini CLI (MCP) — one config entry

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
```

Then add this to your tool's MCP config (file path differs per tool — see the Installation by tool section below):

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

Fully restart the tool. Three new tools appear: `lensify_scan`, `lensify_compact`, `lensify_stats`.

📖 To'liq bosqichma-bosqich ko'rsatmalar **[`USER-INSTALL.md`](../../USER-INSTALL.md)**
---

## Qanday ishlaydi

Skanerlash dvigateli har bir chaqiriqda besh bosqichni ishga tushiradi:

| Phase | What it does | Output |
|---|---|---|
| **1. Walk** | Respects `.gitignore` + vendor exclusions. Categorises every file as code / doc / meta. | File inventory |
| **2. Parse** | Python via stdlib `ast`. JS/TS/Go/Java via regex. Captures imports + public symbols. | Per-file metadata |
| **3. Tier** | Picks T1/T2/T3 from file count, LOC, top-level dirs, monorepo markers. | Token budget |
| **4. Adapt** | Lazy-loads matching framework adapters via manifest. Each emits a typed section. | Framework records |
| **5. Render** | Composes the capsule under tier budget. Writes HTML lens. Caches the result. | Capsule + HTML |

Tipik ish vaqti: o'rta loyihalarda **30 ms**, 500 faylli loyihada **113 ms**.

**Skanerlash uchun ikkita artefakt:**

1. **`LENS.html`** — single self-contained HTML page (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns). For humans — 30-second read.
2. **`LENS.capsule.md`** — Markdown context block, 800–3,600 tokens, framework-aware. For your AI agent — ingested instead of reading 30+ raw files.

---

## Vositaga ko'ra o'rnatish (4 kanal)

To'rtta tarqatish kanali bir xil skanerlash dvigatelini ulashadi.

### Channel 1 — Claude Code / Cowork plugin (recommended)

To'liq tajriba: barcha 5 hook ishga tushadi, slash buyruqlari, statusline, memory loader.

**Cowork:**
1. Download `lensify.plugin` from the [Releases page](https://github.com/agenticailab01/lensify/releases)
2. Drag-and-drop the file into the Cowork chat
3. Click **Save plugin** on the preview card
4. Restart the conversation — you'll see `Lensify dedup is active` confirming installation

**Claude Code (terminal CLI):**
```bash
claude plugin install lensify.plugin
```

Files land at:
- macOS: `~/Library/Application Support/Claude/plugins/lensify/`
- Linux: `~/.local/share/claude/plugins/lensify/`
- Windows: `%APPDATA%\Claude\plugins\lensify\`

### Channel 2 — MCP server (Cursor, VS Code, Codex, Gemini CLI, Antigravity, …)

Sof stdlib JSON-RPC 2.0 stdio server. Serverning o'zi uchun `pip install` qadami kerak emas — u faqat Python standart kutubxonasidan foydalanib, klonlangan repodan to'g'ridan-to'g'ri ishlaydi.

#### Step 1 — Clone the repository

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
cd ~/lensify

# Smoke-test the server (Ctrl-C to exit)
python3 -m mcp_server
```

You should see no output and no errors — the server is now waiting for JSON-RPC requests on stdin. If you see `ModuleNotFoundError`, your Python is older than 3.9; upgrade and retry.

#### Step 2 — Register the server with your tool

Replace `/Users/you/lensify` with the absolute path to your clone.

**Cursor** — `.cursor/mcp.json` (project-local) or `~/.cursor/mcp.json` (global):

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

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "lensify": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/lensify",
      "env": {}
    }
  }
}
```

**VS Code Copilot Chat** — `.vscode/mcp.json` (workspace) or User Settings → `chat.mcp.servers`:

```json
{
  "servers": {
    "lensify": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/lensify"
    }
  }
}
```

**Gemini CLI / Codex / Antigravity** — each tool's MCP config file (same JSON shape as Cursor):

| Tool | Config file |
|---|---|
| Cursor | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) |
| VS Code Copilot Chat | `.vscode/mcp.json` or workspace settings → `chat.mcp.servers` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%\Claude\claude_desktop_config.json` (Win) |
| Gemini CLI | `~/.config/gemini-cli/mcp.json` |
| Codex | `~/.config/codex/mcp.json` |
| Antigravity | Project `.antigravity/mcp.json` or workspace settings |
| OpenCode / Aider with MCP | `~/.config/<tool>/mcp.json` (stdio entry, same shape) |

#### Step 3 — Restart your tool

After saving the config, **fully restart** the tool (not just reload the window). The 3 Lensify tools should appear in your tool's MCP tool picker.

#### The 3 MCP tools

| Tool name | Arguments | What it does |
|---|---|---|
| `lensify_scan` | `path` (str, optional — defaults to cwd), `tier` ("T1" \| "T2" \| "T3" \| "auto"), `no_git` (bool) | Runs a full scan and returns the capsule + path to the generated `LENS.html`. Same engine as `/lensify` in Claude Code. |
| `lensify_compact` | `project_path` (str, optional), `llm` (bool — opt-in LLM narrative) | Generates `WORKING_CONTEXT.md` from current session state. Returns the summary text. |
| `lensify_stats` | (no arguments) | Returns lifetime token-savings counters (scans run, tokens saved, hooks fired). |

Tool descriptions, full parameter schemas, and return types are advertised via the standard MCP `tools/list` and `tools/call` methods — your tool will surface them automatically in its MCP UI.

#### Step 4 — Use it in chat

Once connected, just ask your agent in natural language:

```
"scan this project with Lensify"
"compact this session"
"show me my lensify token savings"
```

Most tools will route those phrases to the matching MCP tool automatically. If the routing isn't picking up, name the tool explicitly: *"use lensify_scan on the current directory."*

#### How the MCP channel differs from the Plugin channel

| Capability | Plugin (Claude Code/Cowork) | MCP server (any tool) |
|---|:---:|:---:|
| `/lensify` scan | ✓ | ✓ (via `lensify_scan`) |
| `/lensify compact` | ✓ | ✓ (via `lensify_compact`) |
| `/lensify stats` | ✓ | ✓ (via `lensify_stats`) |
| Statusline | ✓ | ✗ (tool-specific UI) |
| Skill / slash-commands | ✓ | ✗ (tools invoked by name) |
| 5 session hooks (dedup/inject/compress/memory/activity) | ✓ | ✗ (no hook surface in MCP spec) |
| Cross-session memory loader | ✓ | partial (only via explicit tool call) |

The scan, compact, and stats functionality are identical across both channels — it's the **same Python code under the hood**. What you lose in MCP is the **passive** hook-driven savings (dedup, selective injection, output compression). What you gain is **broad tool support** — anything that speaks MCP can use Lensify.

#### Troubleshooting

| Symptom | Fix |
|---|---|
| Tool doesn't appear in picker | Verify `cwd` is the absolute path to your repo clone. Restart the tool (don't just reload). Check tool's MCP logs (Cursor: View → Output → MCP). |
| `python3: command not found` | Use the full path: `"command": "/usr/bin/python3"` or `"command": "/opt/homebrew/bin/python3"`. |
| Server starts but tools fail | Run `python3 -m mcp_server` manually from `cwd` — if it errors there, fix that error first. |
| JSON-RPC parse errors in logs | A stdout-polluting `print()` snuck into a tool. Re-clone from a clean release tag. |
| Slow first call | Cold-start scan can take 100–250 ms on large repos. Subsequent calls are warm-cached. |

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

## Moslashuvchan darajalar — T1 / T2 / T3

Lensify avtomatik ravishda to'g'ri chuqurlikni tanlaydi.

| Tier | Trigger | Capsule budget | Use case |
|---|---|---:|---|
| **T1 Sketch** | < 50 files · < 5k LOC · single language | 500 tok | Quick scripts, demos, single-file tools |
| **T2 Atlas** | 50–1,000 files · 5k–100k LOC · multi-module | 2,100 tok | Most real projects (the sweet spot) |
| **T3 Compass** | > 1,000 files · monorepo markers · 5+ top-level dirs | 3,600 tok | Monorepos, platforms, enterprise systems |

Chatda bekor qilish maslahatlari:

| Signal | Resulting tier |
|---|---|
| "quick summary" / "gist" / "tldr" | T1 |
| "onboard me" / "explain the project" / default | T2 |
| "monorepo" / "all services" / "full picture" | T3 |

---

## Framework qamrovi — 8 paketdagi 30 adapter

8 paketdagi 30 adapter. Har bir adapter ~80–120 LOC.

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

AI ishlab chiqish loyihasida bitta Lensify skanerlash zanjirning har bir bo'g'inini ochib beradi.

---

## Sessiya hooklari — 5 ishlab chiqarish hooki

5 hook Claude Code sessiyasida birlashadi. Token tejamlari to'planadi.

| Hook | Event | Effect | Approximate savings |
|---|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file — agent gets a "you already saw this at turn N" hint | **~25%** on long sessions |
| `activity_hook.py` | PostToolUse:Edit \| Write \| Bash | Tracks session state; refreshes session capsule every 5 turns | Enables compactor |
| `inject_hook.py` | UserPromptSubmit | Injects only the **relevant** capsule sections per prompt (not the whole capsule) | **~60%** per-prompt savings |
| `compress_hook.py` | PostToolUse:Bash \| WebFetch | Deterministic compression of long tool outputs (HTML/JSON/log/trace/diff/pytest) | Variable, often 80%+ |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work | Carries context across `/clear` boundaries |

**Cowork cheklovi:** Cowork hook yuzasida faqat SessionStart ishga tushadi.

---

## Suhbat siqishtirgich

Uzoq sessiyalar kontekstni iste'mol qiladi. Siqishtirgich soniyalar ichida 8-25k tokenni qaytaradi.

```bash
/lensify compact          # generate WORKING_CONTEXT.md
/clear                        # flush the conversation buffer
# then paste WORKING_CONTEXT.md at the top of the new session
```

Siqishtirgich sessiya holatini o'qiydi va `WORKING_CONTEXT.md` yaratadi:

- Files you touched (with line counts and last operation)
- Bash commands run and their outcomes
- Tests that passed / failed
- Decisions made, open threads
- Optional LLM-enhanced one-paragraph summary if `ANTHROPIC_API_KEY` is set (one Haiku call, ~$0.001)

Bo'sh holat ogohlantirishi: PostToolUse hooklari ishga tushmagan bo'lsa, siqishtirgich aniq tashxis chiqaradi.

---

## Token iqtisodiyoti — aniq raqamlar

Tejamlar qayerdan keladi — aniq raqamlar:

| Stage | Before Lensify | With Lensify | Savings |
|---|---|---|---:|
| Initial orientation | 8,000–20,000 tokens reading 20+ files | One capsule, 800–3,300 tokens | **70–90%** |
| Repeat reads | Each re-read costs full file (≈400 tok / 100 LOC) | Dedup flag, ~0 tokens | **~25%** on long sessions |
| Per-prompt re-injection | Full capsule (2,100 tok) every prompt | Only relevant sections (~800 tok) | **~60%** |
| Long tool outputs | Raw 50 KB Bash output → 12k tokens | Compressed summary + retrieval handle | **80%+** variable |
| Mid-session compaction | `/clear` loses everything | `WORKING_CONTEXT.md` preserves continuity | **8–25k** reclaimable |

**Xarajat misoli (Opus narxi, $15/Mtok kirish):** avval ~$3 turgan 4 soatlik kodlash sessiyasi ~$0,45–$0,90 ga tushadi.

---

## Testlar va samaradorlik byudjetlari

**527 unit test** + **17 CI tomonidan amalga oshirilgan ishlash va xavfsizlik byudjetlari** har bir commitda ishlaydi.

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

## Xavfsizlik va boshqaruv

Lensify is the most security-hardened tool in its category. See [`SECURITY.md`](../../SECURITY.md) for the full threat model.

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

**`/lensify compact --llm` ni aniq ishga tushirmasangiz, hech narsa qurilmadan tashqariga yuborilmaydi**.

For governance — what contributions we accept and what we don't — see [`GOVERNANCE.md`](../../GOVERNANCE.md).

---

## Konfiguratsiya muhit o'zgaruvchilari

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

## Loyiha tuzilishi

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

## Kengaytiring — o'z adapteringizni yozing

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

Full guide: [`skills/lensify/references/adapter-sdk.md`](../../skills/lensify/references/adapter-sdk.md).

### Per-project user adapters (no fork needed)

Drop `.py` files into `<your-project>/.lensify/frameworks/`. They're auto-discovered per scan once you opt in:

```bash
export LENSIFY_USER_ADAPTERS=1
```

The trust decision happens in your shell, not in the code being scanned — protecting you from malicious adapters in untrusted repos.

---

## Muqobillar bilan taqqoslash

Lensify — AI kodlash yordamchilari makonidagi **engil, deterministik yo'naltirish qatlami**.

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

See [`BENCHMARK.md`](../../BENCHMARK.md) for the full competitive analysis.

---

## FAQ

**Q: Does it work on my JS/TS / Go / Rust project?**
J: Asosiy skanerlash JS, TS, Go, Java, Rust va ~20 boshqa tillarda ishlaydi.

**Q: Will it slow down my Claude Code session?**
A: Hook subprocess startup is capped at 250 ms cold (typically 20–30 ms warm). Hook output is capped at 500 tokens per event. Both caps are CI-enforced. The scan itself runs on-demand, not per-prompt.

**Q: Does it send my code anywhere?**
J: Yo'q, agar siz `/lensify compact --llm` ni aniq ishga tushirmasangiz VA `ANTHROPIC_API_KEY` o'rnatilgan bo'lmasa.

**Q: Is the capsule different from a README?**
A: A README tells **humans** what the project does. The capsule tells your **agent** what the project contains: routes, models, training loops, vector indexes, deployments, etc. Different audience, different output, both have their place.

**Q: What if my framework isn't covered by an adapter?**
A: The base scan still produces a useful capsule (entry points, modules, symbols, hotspots, risks). You get less framework-specific noise. Add a custom adapter in ~100 LOC if you want richer output for that framework — see [the adapter SDK guide](../../skills/lensify/references/adapter-sdk.md).

**Q: Can I disable everything and just use the scan?**
A: Yes — `export LENSIFY_DEDUP=0` disables all 5 hooks. The scan engine remains available for explicit `/lensify` invocations.

**Q: Why not use Cursor's @codebase or Sourcegraph Cody instead?**
A: They do **semantic** vector search — they need an embedding model, a vector store, and continuous indexing. Lensify does **structural** extraction — deterministic, fast (sub-second), cheap, and framework-aware. The two are complementary: Lensify for instant orientation, semantic tools for in-depth search.

**Q: How does compaction interact with `/clear`?**
A: Run `/lensify compact` first (generates `WORKING_CONTEXT.md`), then `/clear` to flush the conversation buffer, then paste the contents of `WORKING_CONTEXT.md` at the top of the next session. You resume with the same shoulder-context but a fresh token budget. Compaction typically reclaims 8–25k tokens.

**Q: Is it free?**
J: Ha — MIT litsenziyalangan. Obuna yo'q, telemetriya yo'q.

**Q: How do I uninstall?**
A: Plugin: drag-remove from your tool's plugin manager. MCP: remove the `lensify` entry from your MCP config. CLI: `pip uninstall lensify`. Data: `rm -rf ~/.lensify` and `<project>/.lensify-memory` to wipe everything.

---

## Yo'l xaritasi

| Pack | Status | Notes |
|---|---|---|
| `_ai_apps` v2 — LiteLLM, Instructor, AutoGen | Planned | Next AI-dev sprint |
| `_ml_core` v2 — JAX, Flax, MLX, fastai | Planned | After v2 ai_apps |
| `_serving` v2 — Modal, Replicate, Cog | Planned | |
| `_enterprise` v2 — Django, Flask, Next.js, NestJS | Planned | JS/TS framework coverage |
| Multi-modal lightweight — SQL schemas, shell scripts, Dockerfile, Markdown docs | Investigating | v0.16.0 candidate |
| Optional graph mode — `lensify graph .` + MCP graph queries | Investigating | v0.17.0 candidate |
| `lensify watch` daemon — auto-refresh AGENTS.md on file changes | Investigating | Cross-tool freshness |

GitHub issuelari bilan ovoz bering — nima birinchi kelishi kerak?

---

## Hissa qo'shish va litsenziya

Biz qabul qilamiz:
- New framework adapters (see [`CONTRIBUTING.md`](../../CONTRIBUTING.md))
- Bug fixes with regression tests
- Doc improvements + new integration recipes
- Performance work that keeps the perf budgets green

Biz qabul qilmaymiz:
- `exec`, `eval`, `pickle.loads`, `shell=True`, `os.system` (CI-enforced)
- New outbound HTTP endpoints
- Telemetry or analytics sent off-device
- Adapters with hardcoded credentials or scraping behavior

See [`GOVERNANCE.md`](../../GOVERNANCE.md) for the full policy.

**License:** MIT. © Sachin Patil. See [`LICENSE`](../../LICENSE).

**Maintainer:** Sachin Patil — `agenticailab01@gmail.com`. For security reports, see [`SECURITY.md`](../../SECURITY.md).

---

⭐ Lensify sizga token tejasa, bu repoga yulduzcha qo'ying.
