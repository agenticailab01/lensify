# ProjectLens

> 🌐 **한국어** — 영문판으로: [English](../../README.md)


[![CI](https://github.com/agenticailab01/projectlens/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticailab01/projectlens/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE) [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Version](https://img.shields.io/badge/version-0.15.0-brightgreen.svg)](../../CHANGELOG.md) [![Tests](https://img.shields.io/badge/tests-527%20passing-brightgreen.svg)](#tests--performance) [![Adapters](https://img.shields.io/badge/adapters-30%20across%208%20packs-blue.svg)](#framework-coverage)

> **AI 코딩 에이전트를 위한 단일 스캔 적응형 프로젝트 렌즈 + 토큰 최적화 컨텍스트 캡슐.** 방향 설정 토큰을 70–90% 절감. AI 개발 라이프사이클 전반에 걸친 프레임워크 인식. 순수 표준 라이브러리. MIT 라이선스.

**📖 당신의 언어로 읽기:** 🇬🇧 [← 영문판으로](../../README.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇹🇼 [繁體中文](README.zh-TW.md) · 🇯🇵 [日本語](README.ja.md) · 🇩🇪 [Deutsch](README.de.md) · 🇫🇷 [Français](README.fr.md) · 🇪🇸 [Español](README.es.md) · 🇮🇳 [हिन्दी](README.hi.md) · 🇧🇷 [Português](README.pt.md) · 🇷🇺 [Русский](README.ru.md) · 🇸🇦 [العربية](README.ar.md) · 🇮🇹 [Italiano](README.it.md) · 🇵🇱 [Polski](README.pl.md) · 🇳🇱 [Nederlands](README.nl.md) · 🇹🇷 [Türkçe](README.tr.md) · 🇺🇦 [Українська](README.uk.md) · 🇻🇳 [Tiếng Việt](README.vi.md) · 🇮🇩 [Bahasa Indonesia](README.id.md) · 🇸🇪 [Svenska](README.sv.md) · 🇬🇷 [Ελληνικά](README.el.md) · 🇷🇴 [Română](README.ro.md) · 🇨🇿 [Čeština](README.cs.md) · 🇫🇮 [Suomi](README.fi.md) · 🇩🇰 [Dansk](README.da.md) · 🇳🇴 [Norsk](README.no.md) · 🇭🇺 [Magyar](README.hu.md) · 🇹🇭 [ภาษาไทย](README.th.md) · 🇺🇿 [O'zbekcha](README.uz.md)

---

## 목차

1. [ProjectLens를 선택하는 이유](#why-projectlens)
2. [한눈에 보기](#at-a-glance)
3. [빠른 시작](#quick-start)
4. [작동 원리](#how-it-works)
5. [도구별 설치 (4가지 채널)](#installation-by-tool)
6. [적응형 계층 — T1 / T2 / T3](#adaptive-tiers)
7. [프레임워크 커버리지 — 8개 팩의 30개 어댑터](#framework-coverage)
8. [세션 후크 — 5개의 프로덕션 후크](#session-hooks)
9. [대화 압축기](#conversation-compactor)
10. [토큰 경제학 — 구체적인 숫자](#token-economics)
11. [테스트 및 성능 예산](#tests--performance)
12. [보안 및 거버넌스](#security--governance)
13. [구성 환경 변수](#configuration)
14. [프로젝트 구조](#project-structure)
15. [확장 — 자신만의 어댑터 작성](#extending-projectlens)
16. [대안과의 비교](#comparison)
17. [FAQ](#faq)
18. [로드맵](#roadmap)
19. [기여 및 라이선스](#contributing--license)

---

## ProjectLens를 선택하는 이유

최신 AI 코딩 에이전트에는 컨텍스트 윈도우 문제가 있습니다: 프로젝트가 클수록 단지 **자기 정향**에 더 많은 토큰을 소비합니다. 일반적인 온보딩 흐름에서는 에이전트가 유용한 작업을 하기 전에 20~40개의 파일을 읽어야 하며 — 이는 10~30k 토큰이 사용자의 실제 문제 해결이 아닌 이해에 소비되는 것을 의미합니다.

ProjectLens는 그 정향 단계를 **단일 스캔**(100ms 미만)으로 대체하여 토큰 제한 프레임워크 인식 컨텍스트 블록을 생성합니다. 에이전트는 수십 개의 파일 대신 **하나의 캡슐**을 읽습니다. 정향 절약만으로 토큰 사용량이 70~90% 줄어들며, 5개의 세션 후크가 그 위에 추가 절약을 쌓아 올립니다.

**상충 관계:** 시맨틱 벡터 검색(더 느리고 임베딩 비용이 들고 일반적임) 대신 결정론적 구조 추출(빠르고 무료이며 프레임워크 인식)을 선택합니다. ProjectLens는 Cursor의 `@codebase` 및 Sourcegraph Cody와 같은 시맨틱 도구와 충돌하지 않고 함께 작동합니다. 즉각적인 정향에는 ProjectLens를 사용하고, 에이전트가 구조가 아닌 의미로 특정 항목을 찾아야 할 때는 시맨틱 검색을 사용하세요.

---

## 한눈에 보기

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

## 빠른 시작

ProjectLens has **three install paths**. Pick the one that matches your tool — every path takes under a minute.

### 👉 Claude Code (terminal) — one command in chat

```
/plugin marketplace add agenticailab01/projectlens
/plugin install projectlens@projectlens
```

Then in any project: `/projectlens` to scan, `/projectlens compact` to recover tokens, `/projectlens stats` for savings.

### 👉 Cowork (desktop app) — drag and drop

1. Download `projectlens.plugin` from the [Releases page](https://github.com/agenticailab01/projectlens/releases).
2. Drag the file into the Cowork chat window.
3. Click **Save plugin** on the preview card. Restart the conversation.

### 👉 Cursor / VS Code / Codex / Gemini CLI (MCP) — one config entry

```bash
git clone https://github.com/agenticailab01/projectlens ~/projectlens
```

Then add this to your tool's MCP config (file path differs per tool — see the Installation by tool section below):

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/projectlens"
    }
  }
}
```

Fully restart the tool. Three new tools appear: `projectlens_scan`, `projectlens_compact`, `projectlens_stats`.

📖 전체 단계별 지침은 **[`USER-INSTALL.md`](../../USER-INSTALL.md)**
---

## 작동 원리

스캔 엔진은 호출당 5단계를 실행합니다:

| Phase | What it does | Output |
|---|---|---|
| **1. Walk** | Respects `.gitignore` + vendor exclusions. Categorises every file as code / doc / meta. | File inventory |
| **2. Parse** | Python via stdlib `ast`. JS/TS/Go/Java via regex. Captures imports + public symbols. | Per-file metadata |
| **3. Tier** | Picks T1/T2/T3 from file count, LOC, top-level dirs, monorepo markers. | Token budget |
| **4. Adapt** | Lazy-loads matching framework adapters via manifest. Each emits a typed section. | Framework records |
| **5. Render** | Composes the capsule under tier budget. Writes HTML lens. Caches the result. | Capsule + HTML |

일반적 런타임: 중간 규모 프로젝트에서 **30ms**, 500개 파일 프로젝트에서 **113ms**. 스캔은 단계 간에 파일을 재읽기하지 않습니다.

**스캔당 두 가지 산출물:**

1. **`LENS.html`** — single self-contained HTML page (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns). For humans — 30-second read.
2. **`LENS.capsule.md`** — Markdown context block, 800–3,600 tokens, framework-aware. For your AI agent — ingested instead of reading 30+ raw files.

---

## 도구별 설치 (4가지 채널)

4개의 배포 채널이 동일한 스캔 엔진을 공유합니다. 사용 도구에 맞는 채널을 선택하세요.

### Channel 1 — Claude Code / Cowork plugin (recommended)

전체 경험: 5개 후크 모두 작동, 슬래시 명령, 상태 표시줄, 메모리 로더.

**Cowork:**
1. Download `projectlens.plugin` from the [Releases page](https://github.com/agenticailab01/projectlens/releases)
2. Drag-and-drop the file into the Cowork chat
3. Click **Save plugin** on the preview card
4. Restart the conversation — you'll see `ProjectLens dedup is active` confirming installation

**Claude Code (terminal CLI):**
```bash
claude plugin install projectlens.plugin
```

Files land at:
- macOS: `~/Library/Application Support/Claude/plugins/projectlens/`
- Linux: `~/.local/share/claude/plugins/projectlens/`
- Windows: `%APPDATA%\Claude\plugins\projectlens\`

### Channel 2 — MCP server (Cursor, VS Code, Codex, Gemini CLI, Antigravity, …)

순수 표준 라이브러리 JSON-RPC 2.0 stdio 서버. 서버 자체에는 `pip install` 단계가 필요 없습니다 — Python 표준 라이브러리만 사용하여 복제된 저장소에서 직접 실행됩니다.

#### Step 1 — Clone the repository

```bash
git clone https://github.com/agenticailab01/projectlens ~/projectlens
cd ~/projectlens

# Smoke-test the server (Ctrl-C to exit)
python3 -m mcp_server
```

You should see no output and no errors — the server is now waiting for JSON-RPC requests on stdin. If you see `ModuleNotFoundError`, your Python is older than 3.9; upgrade and retry.

#### Step 2 — Register the server with your tool

Replace `/Users/you/projectlens` with the absolute path to your clone.

**Cursor** — `.cursor/mcp.json` (project-local) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/projectlens"
    }
  }
}
```

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/projectlens",
      "env": {}
    }
  }
}
```

**VS Code Copilot Chat** — `.vscode/mcp.json` (workspace) or User Settings → `chat.mcp.servers`:

```json
{
  "servers": {
    "projectlens": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/projectlens"
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

After saving the config, **fully restart** the tool (not just reload the window). The 3 ProjectLens tools should appear in your tool's MCP tool picker.

#### The 3 MCP tools

| Tool name | Arguments | What it does |
|---|---|---|
| `projectlens_scan` | `path` (str, optional — defaults to cwd), `tier` ("T1" \| "T2" \| "T3" \| "auto"), `no_git` (bool) | Runs a full scan and returns the capsule + path to the generated `LENS.html`. Same engine as `/projectlens` in Claude Code. |
| `projectlens_compact` | `project_path` (str, optional), `llm` (bool — opt-in LLM narrative) | Generates `WORKING_CONTEXT.md` from current session state. Returns the summary text. |
| `projectlens_stats` | (no arguments) | Returns lifetime token-savings counters (scans run, tokens saved, hooks fired). |

Tool descriptions, full parameter schemas, and return types are advertised via the standard MCP `tools/list` and `tools/call` methods — your tool will surface them automatically in its MCP UI.

#### Step 4 — Use it in chat

Once connected, just ask your agent in natural language:

```
"scan this project with ProjectLens"
"compact this session"
"show me my projectlens token savings"
```

Most tools will route those phrases to the matching MCP tool automatically. If the routing isn't picking up, name the tool explicitly: *"use projectlens_scan on the current directory."*

#### How the MCP channel differs from the Plugin channel

| Capability | Plugin (Claude Code/Cowork) | MCP server (any tool) |
|---|:---:|:---:|
| `/projectlens` scan | ✓ | ✓ (via `projectlens_scan`) |
| `/projectlens compact` | ✓ | ✓ (via `projectlens_compact`) |
| `/projectlens stats` | ✓ | ✓ (via `projectlens_stats`) |
| Statusline | ✓ | ✗ (tool-specific UI) |
| Skill / slash-commands | ✓ | ✗ (tools invoked by name) |
| 5 session hooks (dedup/inject/compress/memory/activity) | ✓ | ✗ (no hook surface in MCP spec) |
| Cross-session memory loader | ✓ | partial (only via explicit tool call) |

The scan, compact, and stats functionality are identical across both channels — it's the **same Python code under the hood**. What you lose in MCP is the **passive** hook-driven savings (dedup, selective injection, output compression). What you gain is **broad tool support** — anything that speaks MCP can use ProjectLens.

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
pip install projectlens
projectlens --version
projectlens . --no-git
```

Available flags:
- `--tier T1|T2|T3|auto` — force a complexity tier (default: auto)
- `--capsule-only` — skip HTML, write only the Markdown capsule
- `--ast-only` — deterministic mode, no LLM enrichment of narrative
- `--no-git` — skip git hotspot analysis (faster)
- `--output <dir>` — override output directory (default: `<target>/projectlens-out`)
- `--install-agents-md [FILE]` — append/update capsule inside a context file (default: `AGENTS.md`)
- `--version` — print version and exit

### Channel 4 — AGENTS.md write mode (any tool that reads context files)

```bash
projectlens . --install-agents-md              # writes AGENTS.md
projectlens . --install-agents-md CLAUDE.md
projectlens . --install-agents-md GEMINI.md
projectlens . --install-agents-md .cursorrules
```

The capsule lands inside the target file wrapped in idempotent `<!-- projectlens-begin -->` / `<!-- projectlens-end -->` markers. Re-running replaces only the marked block; any other content you've added is preserved.

---

## 적응형 계층 — T1 / T2 / T3

ProjectLens는 적절한 깊이를 자동으로 선택합니다. 강력한 이유가 있을 때만 `--tier T1|T2|T3`로 재정의하세요.

| Tier | Trigger | Capsule budget | Use case |
|---|---|---:|---|
| **T1 Sketch** | < 50 files · < 5k LOC · single language | 500 tok | Quick scripts, demos, single-file tools |
| **T2 Atlas** | 50–1,000 files · 5k–100k LOC · multi-module | 2,100 tok | Most real projects (the sweet spot) |
| **T3 Compass** | > 1,000 files · monorepo markers · 5+ top-level dirs | 3,600 tok | Monorepos, platforms, enterprise systems |

채팅 내 재정의 힌트 — ProjectLens는 의도를 읽습니다:

| Signal | Resulting tier |
|---|---|
| "quick summary" / "gist" / "tldr" | T1 |
| "onboard me" / "explain the project" / default | T2 |
| "monorepo" / "all services" / "full picture" | T3 |

---

## 프레임워크 커버리지 — 8개 팩의 30개 어댑터

8개 팩에 걸친 30개의 어댑터. 각 어댑터는 약 80~120 LOC이며, 프레임워크 서명이 프로젝트와 일치할 때만 지연 로드됩니다.

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

AI 개발 프로젝트에 대한 단일 ProjectLens 스캔은 체인의 모든 링크를 드러냅니다: 원시 노트북에서 학습, 모델링, 임베딩, 에이전틱 오케스트레이션, UI 구성 요소 및 프로덕션 배포까지 — 모두 **하나의 캡슐**, 예산 내에서.

---

## 세션 후크 — 5개의 프로덕션 후크

5개의 후크는 Claude Code 세션 전체에서 복합적으로 작용합니다. 토큰 절약은 세션의 수명 전반에 걸쳐 누적됩니다.

| Hook | Event | Effect | Approximate savings |
|---|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file — agent gets a "you already saw this at turn N" hint | **~25%** on long sessions |
| `activity_hook.py` | PostToolUse:Edit \| Write \| Bash | Tracks session state; refreshes session capsule every 5 turns | Enables compactor |
| `inject_hook.py` | UserPromptSubmit | Injects only the **relevant** capsule sections per prompt (not the whole capsule) | **~60%** per-prompt savings |
| `compress_hook.py` | PostToolUse:Bash \| WebFetch | Deterministic compression of long tool outputs (HTML/JSON/log/trace/diff/pytest) | Variable, often 80%+ |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work | Carries context across `/clear` boundaries |

**Cowork 제한:** Cowork의 후크 표면에서는 SessionStart만 작동합니다. 스캔 엔진, 캡슐 생성 및 `/projectlens compact`는 여전히 작동하지만 — 5개의 후크 기반 최적화는 Claude Code의 터미널 CLI에서만 활성화됩니다.

---

## 대화 압축기

긴 세션은 컨텍스트를 소비합니다. 압축기는 몇 초 안에 8~25k 토큰을 회수합니다.

```bash
/projectlens compact          # generate WORKING_CONTEXT.md
/clear                        # flush the conversation buffer
# then paste WORKING_CONTEXT.md at the top of the new session
```

압축기는 `activity_hook`이 기록한 세션 상태를 읽고 다음을 요약한 `WORKING_CONTEXT.md`를 생성합니다:

- Files you touched (with line counts and last operation)
- Bash commands run and their outcomes
- Tests that passed / failed
- Decisions made, open threads
- Optional LLM-enhanced one-paragraph summary if `ANTHROPIC_API_KEY` is set (one Haiku call, ~$0.001)

빈 상태 경고: PostToolUse 후크가 발화하지 않은 경우(Cowork에서 일반적), 압축기는 작업을 캡처한 척하지 않고 명확한 진단을 출력합니다.

---

## 토큰 경제학 — 구체적인 숫자

절약이 어디에서 오는가 — 프로덕션 사용에서의 구체적인 숫자:

| Stage | Before ProjectLens | With ProjectLens | Savings |
|---|---|---|---:|
| Initial orientation | 8,000–20,000 tokens reading 20+ files | One capsule, 800–3,300 tokens | **70–90%** |
| Repeat reads | Each re-read costs full file (≈400 tok / 100 LOC) | Dedup flag, ~0 tokens | **~25%** on long sessions |
| Per-prompt re-injection | Full capsule (2,100 tok) every prompt | Only relevant sections (~800 tok) | **~60%** |
| Long tool outputs | Raw 50 KB Bash output → 12k tokens | Compressed summary + retrieval handle | **80%+** variable |
| Mid-session compaction | `/clear` loses everything | `WORKING_CONTEXT.md` preserves continuity | **8–25k** reclaimable |

**비용 예시(Opus 가격, $15/Mtok 입력):** 이전에 입력 토큰에 약 $3가 들었던 4시간 코딩 세션은 모든 후크가 활성화된 경우 약 $0.45~$0.90로 떨어집니다.

---

## 테스트 및 성능 예산

**527개의 단위 테스트** + **17개의 CI 강제 성능 및 보안 예산**이 모든 커밋마다 macOS / Linux / Windows × Python 3.9~3.12에서 실행됩니다.

합성 프로젝트 크기에서 측정된 성능:

| Project size | Files | Scan time | Capsule size | Sections rendered |
|---|---:|---:|---:|---:|
| Tiny | 20 | **41 ms** | 402 tok | 5 |
| Medium | 100 | **29 ms** | 529 tok | 5 |
| Large | 500 | **113 ms** | 529 tok | 5 |

캡슐 크기는 **프로젝트 크기와 무관하게 계층 예산에 제한**됩니다 — 선형 스캔 시간, 일정한 출력. 이것이 아키텍처적 해자입니다.

CI에서 강제되는 하드 캡:

| Operation | Hard cap |
|---|---|
| Hook subprocess startup | < 250 ms |
| Scan on 100-file fixture | < 2.5 s |
| Capsule build | < 200 ms |
| Hook output envelope | ≤ 500 tokens per event |
| `SKILL.md` size | < 8 KB |
| Rule R1 — hooks framework-free | static-analysis enforced |
| Rule R3 — `detect()` never opens files | static-analysis enforced |

어댑터를 추가해도 이 중 어느 것도 후퇴할 수 없습니다. 예산을 위반하는 Pull Request는 CI에서 실패합니다.

---

## 보안 및 거버넌스

ProjectLens is the most security-hardened tool in its category. See [`SECURITY.md`](../../SECURITY.md) for the full threat model.

**CI-enforced safety:**
- `exec()`, `eval()`, `__import__()`, `pickle.loads()`, `marshal.loads()`, `shell=True`, `os.system()` are **statically banned** in shipped code
- Outbound HTTP confined to a single allowlisted endpoint (`api.anthropic.com`) inside `llm_client.py`
- User-defined adapter loader is **opt-in** via `PROJECTLENS_USER_ADAPTERS=1` (off by default — scanning a malicious repo cannot execute arbitrary Python without explicit user opt-in)
- 1 MB per-file read cap prevents DoS via huge files
- 30-second `git` subprocess timeout

**What's persisted locally:**

| Data | Location | Lifetime | Opt-out |
|---|---|---|---|
| Lifetime stats counters | `~/.projectlens/stats.json` | Permanent | `PROJECTLENS_STATS=0` |
| Cross-session memory | `<project>/.projectlens-memory/*.json` | Per-project, max 50 (LRU) | `PROJECTLENS_MEMORY=0` |
| Session state | `<project>/projectlens-out/state.json` | Per-session | `PROJECTLENS_DEDUP=0` |
| Capsule + lens artefacts | `<project>/projectlens-out/` | Regenerated each scan | n/a |

**`/projectlens compact --llm`을 명시적으로 실행하지 않는 한 어떤 것도 장치 외부로 전송되지 않습니다.** 통계 및 메모리 파일은 일반 JSON입니다 — 감사 가능, 삭제 가능, PII 없음.

For governance — what contributions we accept and what we don't — see [`GOVERNANCE.md`](../../GOVERNANCE.md).

---

## 구성 환경 변수

모든 영구 표면에는 문서화된 환경 변수 옵트아웃이 있습니다:

```bash
# Hook control
export PROJECTLENS_DEDUP=0              # disable ALL hooks (dedup/activity/inject/compress/memory)
export PROJECTLENS_COMPRESS_OUTPUT=0    # disable just output compression

# Persistence control
export PROJECTLENS_STATS=0              # disable lifetime stats counters
export PROJECTLENS_STATS_HOME=/path     # change where stats live (default ~/.projectlens)
export PROJECTLENS_MEMORY=0             # disable cross-session memory

# Resource limits
export PROJECTLENS_MAX_READ_BYTES=N     # per-file read cap in bytes (default 1MB)

# Trust gating (opt-in only)
export PROJECTLENS_USER_ADAPTERS=1      # opt IN to user-defined adapters from <project>/.projectlens/frameworks/

# Optional LLM enhancement
export ANTHROPIC_API_KEY=sk-...         # enables /projectlens compact --llm narrative
```

다시 활성화하려면 설정 해제하세요. 다른 모든 것은 변경되지 않습니다 — 플러그인 파일이 이동되지 않고 데이터가 손실되지 않습니다.

---

## 프로젝트 구조

```
projectlens/
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
├── skills/projectlens/
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

## 확장 — 자신만의 어댑터 작성

어댑터 SDK는 의도적으로 작습니다. 각 어댑터는 약 80~120 LOC입니다.

### Write a new framework adapter

```bash
cd skills/projectlens/scripts/frameworks
cp -r _template _myframework
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes
$EDITOR manifest.json                    # register entry
$EDITOR ../../../../tests/test_myframework.py   # add tests
```

모든 어댑터가 따라야 하는 계약:

| Rule | What |
|---|---|
| **R1** | Hook scripts never import from `frameworks/*` (CI-enforced) |
| **R2** | Adapter modules stay small — ~80–120 LOC |
| **R3** | `detect()` is O(1) — never opens files (CI-enforced) |
| **R4** | `extract()` reads only files that match your framework's signature |
| **R5** | `capsule_section()` respects `budget_tokens` |

Full guide: [`skills/projectlens/references/adapter-sdk.md`](../../skills/projectlens/references/adapter-sdk.md).

### Per-project user adapters (no fork needed)

`<your-project>/.projectlens/frameworks/`에 `.py` 파일을 드롭하세요. 옵트인하면 스캔마다 자동으로 검색됩니다:

```bash
export PROJECTLENS_USER_ADAPTERS=1
```

신뢰 결정은 스캔되는 코드가 아니라 셸에서 이루어집니다 — 신뢰할 수 없는 저장소의 악성 어댑터로부터 사용자를 보호합니다.

---

## 대안과의 비교

ProjectLens는 AI 코딩 어시스턴트 공간에서 **가볍고 결정론적인 정향 계층**입니다. 시맨틱 검색 도구를 대체하지 않고 보완합니다.

| Capability | Repomix | Aider repo-map | Cursor `@codebase` | Sourcegraph Cody | Graphify | Caveman | **ProjectLens** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Single-pass summary | ✓ | ✓ | ✓ (search) | ✓ (search) | ✓ | ✓ | **✓** |
| Token-bounded output | ~ | ~ | ✗ | ✗ | ✗ | ~ | **✓ tier-locked** |
| Adaptive depth (auto-tier) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ T1/T2/T3** |
| Framework-aware extraction | ✗ | ✗ | ~ | ~ | ✗ | ~ | **✓ 30 adapters** |
| Confidence tags on output | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ EXTRACTED/INFERRED/AMBIGUOUS** |
| In-session hooks | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ 5 hooks** |
| Mid-session compaction | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ /projectlens compact** |
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
A: 기본 스캔(파일 워크, 언어 감지, 심볼)은 JS, TS, Go, Java, Rust, Ruby, PHP, C/C++ 및 ~20개의 다른 언어에서 작동합니다. 현재 30개의 프레임워크별 어댑터는 주로 Python 중심이며, Vue SFC + Tailwind + Docker Compose가 JS/Web 측을 다룹니다. JS/TS 프레임워크 어댑터(Next.js, Astro, SvelteKit, NestJS)는 로드맵에 있습니다.

**Q: Will it slow down my Claude Code session?**
A: 후크 서브프로세스 시작은 콜드 250ms로 제한됩니다(일반적으로 웜 20~30ms). 후크 출력은 이벤트당 500 토큰으로 제한됩니다. 두 제한 모두 CI에서 강제됩니다. 스캔 자체는 프롬프트당이 아니라 요청 시 실행됩니다.

**Q: Does it send my code anywhere?**
A: 아니요, 명시적으로 `/projectlens compact --llm`을 실행하고 **AND** `ANTHROPIC_API_KEY`가 설정된 경우를 제외하고는 그렇지 않습니다. 그 경우에도 세션 활동 요약(파일 경로, 명령 이름, 테스트 결과)만 전송되며 — 파일 내용은 결코 전송되지 않습니다.

**Q: Is the capsule different from a README?**
A: README는 프로젝트가 무엇을 하는지 **인간**에게 알려줍니다. 캡슐은 프로젝트에 무엇이 포함되어 있는지 **에이전트**에게 알려줍니다: 라우트, 모델, 훈련 루프, 벡터 인덱스, 배포 등. 다른 대상, 다른 출력, 둘 다 자리가 있습니다.

**Q: What if my framework isn't covered by an adapter?**
A: The base scan still produces a useful capsule (entry points, modules, symbols, hotspots, risks). You get less framework-specific noise. Add a custom adapter in ~100 LOC if you want richer output for that framework — see [the adapter SDK guide](../../skills/projectlens/references/adapter-sdk.md).

**Q: Can I disable everything and just use the scan?**
A: Yes — `export PROJECTLENS_DEDUP=0` disables all 5 hooks. The scan engine remains available for explicit `/projectlens` invocations.

**Q: Why not use Cursor's @codebase or Sourcegraph Cody instead?**
A: They do **semantic** vector search — they need an embedding model, a vector store, and continuous indexing. ProjectLens does **structural** extraction — deterministic, fast (sub-second), cheap, and framework-aware. The two are complementary: ProjectLens for instant orientation, semantic tools for in-depth search.

**Q: How does compaction interact with `/clear`?**
A: Run `/projectlens compact` first (generates `WORKING_CONTEXT.md`), then `/clear` to flush the conversation buffer, then paste the contents of `WORKING_CONTEXT.md` at the top of the next session. You resume with the same shoulder-context but a fresh token budget. Compaction typically reclaims 8–25k tokens.

**Q: Is it free?**
A: 네 — MIT 라이선스. 구독 없음, 장치 외부 텔레메트리 없음, 필수 pip 종속성 없음.

**Q: How do I uninstall?**
A: Plugin: drag-remove from your tool's plugin manager. MCP: remove the `projectlens` entry from your MCP config. CLI: `pip uninstall projectlens`. Data: `rm -rf ~/.projectlens` and `<project>/.projectlens-memory` to wipe everything.

---

## 로드맵

| Pack | Status | Notes |
|---|---|---|
| `_ai_apps` v2 — LiteLLM, Instructor, AutoGen | Planned | Next AI-dev sprint |
| `_ml_core` v2 — JAX, Flax, MLX, fastai | Planned | After v2 ai_apps |
| `_serving` v2 — Modal, Replicate, Cog | Planned | |
| `_enterprise` v2 — Django, Flask, Next.js, NestJS | Planned | JS/TS framework coverage |
| Multi-modal lightweight — SQL schemas, shell scripts, Dockerfile, Markdown docs | Investigating | v0.16.0 candidate |
| Optional graph mode — `projectlens graph .` + MCP graph queries | Investigating | v0.17.0 candidate |
| `projectlens watch` daemon — auto-refresh AGENTS.md on file changes | Investigating | Cross-tool freshness |

GitHub 이슈로 투표하세요 — 무엇이 먼저 와야 합니까?

---

## 기여 및 라이선스

우리가 환영하는 것:
- New framework adapters (see [`CONTRIBUTING.md`](../../CONTRIBUTING.md))
- Bug fixes with regression tests
- Doc improvements + new integration recipes
- Performance work that keeps the perf budgets green

우리가 받아들이지 않는 것:
- `exec`, `eval`, `pickle.loads`, `shell=True`, `os.system` (CI-enforced)
- New outbound HTTP endpoints
- Telemetry or analytics sent off-device
- Adapters with hardcoded credentials or scraping behavior

See [`GOVERNANCE.md`](../../GOVERNANCE.md) for the full policy.

**License:** MIT. © Sachin Patil. See [`LICENSE`](../../LICENSE).

**Maintainer:** Sachin Patil — `agenticailab01@gmail.com`. For security reports, see [`SECURITY.md`](../../SECURITY.md).

---

⭐ ProjectLens가 토큰을 절약해 준다면 이 저장소에 별을 눌러주세요. 사용하는 프레임워크가 다뤄지지 않으면 이슈를 열어주세요 — 대부분의 어댑터는 약 100 LOC이며 우선시할 것입니다.
