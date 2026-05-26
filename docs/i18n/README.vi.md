# ProjectLens

> 🌐 **Tiếng Việt** — Quay lại tiếng Anh: [English](../../README.md)


[![CI](https://github.com/agenticailab01/projectlens/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticailab01/projectlens/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE) [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Version](https://img.shields.io/badge/version-0.15.0-brightgreen.svg)](../../CHANGELOG.md) [![Tests](https://img.shields.io/badge/tests-527%20passing-brightgreen.svg)](#tests--performance) [![Adapters](https://img.shields.io/badge/adapters-30%20across%208%20packs-blue.svg)](#framework-coverage)

> **Thấu kính dự án thích ứng một lần quét + viên nang ngữ cảnh được tối ưu hóa token cho các tác nhân lập trình AI.** Giảm 70–90% token định hướng. Nhận biết framework trên toàn bộ vòng đời phát triển AI. Thư viện chuẩn thuần. Giấy phép MIT.

**📖 Đọc bằng ngôn ngữ của bạn:** 🇬🇧 [← Quay lại tiếng Anh](../../README.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇹🇼 [繁體中文](README.zh-TW.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇩🇪 [Deutsch](README.de.md) · 🇫🇷 [Français](README.fr.md) · 🇪🇸 [Español](README.es.md) · 🇮🇳 [हिन्दी](README.hi.md) · 🇧🇷 [Português](README.pt.md) · 🇷🇺 [Русский](README.ru.md) · 🇸🇦 [العربية](README.ar.md) · 🇮🇹 [Italiano](README.it.md) · 🇵🇱 [Polski](README.pl.md) · 🇳🇱 [Nederlands](README.nl.md) · 🇹🇷 [Türkçe](README.tr.md) · 🇺🇦 [Українська](README.uk.md) · 🇮🇩 [Bahasa Indonesia](README.id.md) · 🇸🇪 [Svenska](README.sv.md) · 🇬🇷 [Ελληνικά](README.el.md) · 🇷🇴 [Română](README.ro.md) · 🇨🇿 [Čeština](README.cs.md) · 🇫🇮 [Suomi](README.fi.md) · 🇩🇰 [Dansk](README.da.md) · 🇳🇴 [Norsk](README.no.md) · 🇭🇺 [Magyar](README.hu.md) · 🇹🇭 [ภาษาไทย](README.th.md) · 🇺🇿 [O'zbekcha](README.uz.md)

---

## Mục lục

1. [Tại sao ProjectLens](#why-projectlens)
2. [Tổng quan](#at-a-glance)
3. [Bắt đầu nhanh](#quick-start)
4. [Cách hoạt động](#how-it-works)
5. [Cài đặt theo công cụ (4 kênh)](#installation-by-tool)
6. [Cấp độ thích ứng — T1 / T2 / T3](#adaptive-tiers)
7. [Phạm vi framework — 30 adapter trong 8 gói](#framework-coverage)
8. [Hooks phiên — 5 hooks sản xuất](#session-hooks)
9. [Bộ nén hội thoại](#conversation-compactor)
10. [Kinh tế token — con số cụ thể](#token-economics)
11. [Kiểm thử và ngân sách hiệu suất](#tests--performance)
12. [Bảo mật và quản trị](#security--governance)
13. [Biến môi trường cấu hình](#configuration)
14. [Cấu trúc dự án](#project-structure)
15. [Mở rộng — viết adapter của riêng bạn](#extending-projectlens)
16. [So sánh với các lựa chọn thay thế](#comparison)
17. [FAQ](#faq)
18. [Lộ trình](#roadmap)
19. [Đóng góp và giấy phép](#contributing--license)

---

## Tại sao ProjectLens

Các tác nhân lập trình AI hiện đại có vấn đề cửa sổ ngữ cảnh: dự án càng lớn, chúng càng đốt nhiều token chỉ để **tự định hướng**. Quy trình onboarding điển hình đọc 20-40 tệp trước khi tác nhân có thể làm việc hữu ích — đó là 10-30k token dùng để hiểu, không phải giải quyết vấn đề thực tế của người dùng.

ProjectLens thay thế giai đoạn định hướng đó bằng **một lần quét duy nhất** (dưới 100 ms) tạo ra khối ngữ cảnh giới hạn token, nhận biết framework. Tác nhân đọc **một viên nang** thay vì hàng chục tệp. Việc sử dụng token giảm 70-90% chỉ từ tiết kiệm định hướng — và 5 hook phiên xếp chồng tiết kiệm bổ sung lên trên.

**Sự đánh đổi nó thực hiện:** trích xuất cấu trúc xác định (nhanh, miễn phí, nhận biết framework) thay vì tìm kiếm vector ngữ nghĩa (chậm hơn, chi phí embedding, chung chung). ProjectLens hoạt động cùng với các công cụ ngữ nghĩa như `@codebase` của Cursor và Sourcegraph Cody — không chống lại chúng. Sử dụng ProjectLens để định hướng tức thì; chuyển sang tìm kiếm ngữ nghĩa khi tác nhân cần tìm thứ gì đó cụ thể theo ý nghĩa thay vì cấu trúc.

---

## Tổng quan

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

## Bắt đầu nhanh

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

📖 Hướng dẫn từng bước đầy đủ trong **[`USER-INSTALL.md`](../../USER-INSTALL.md)**
---

## Cách hoạt động

Công cụ quét chạy năm giai đoạn mỗi lần gọi:

| Phase | What it does | Output |
|---|---|---|
| **1. Walk** | Respects `.gitignore` + vendor exclusions. Categorises every file as code / doc / meta. | File inventory |
| **2. Parse** | Python via stdlib `ast`. JS/TS/Go/Java via regex. Captures imports + public symbols. | Per-file metadata |
| **3. Tier** | Picks T1/T2/T3 from file count, LOC, top-level dirs, monorepo markers. | Token budget |
| **4. Adapt** | Lazy-loads matching framework adapters via manifest. Each emits a typed section. | Framework records |
| **5. Render** | Composes the capsule under tier budget. Writes HTML lens. Caches the result. | Capsule + HTML |

Thời gian chạy điển hình: **30 ms** trên các dự án trung bình, **113 ms** trên dự án 500 tệp. Quét không bao giờ đọc lại tệp giữa các giai đoạn.

**Hai sản phẩm mỗi lần quét:**

1. **`LENS.html`** — single self-contained HTML page (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns). For humans — 30-second read.
2. **`LENS.capsule.md`** — Markdown context block, 800–3,600 tokens, framework-aware. For your AI agent — ingested instead of reading 30+ raw files.

---

## Cài đặt theo công cụ (4 kênh)

Bốn kênh phân phối chia sẻ cùng một công cụ quét. Chọn cái phù hợp với công cụ của bạn.

### Channel 1 — Claude Code / Cowork plugin (recommended)

Trải nghiệm đầy đủ: tất cả 5 hook kích hoạt, lệnh slash, statusline, memory loader.

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

Máy chủ JSON-RPC 2.0 stdio thuần stdlib. Không cần bước `pip install` cho máy chủ — nó chạy trực tiếp từ repo đã clone chỉ sử dụng thư viện chuẩn Python.

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

## Cấp độ thích ứng — T1 / T2 / T3

ProjectLens tự động chọn độ sâu phù hợp. Ghi đè bằng `--tier T1|T2|T3` chỉ khi bạn có lý do mạnh.

| Tier | Trigger | Capsule budget | Use case |
|---|---|---:|---|
| **T1 Sketch** | < 50 files · < 5k LOC · single language | 500 tok | Quick scripts, demos, single-file tools |
| **T2 Atlas** | 50–1,000 files · 5k–100k LOC · multi-module | 2,100 tok | Most real projects (the sweet spot) |
| **T3 Compass** | > 1,000 files · monorepo markers · 5+ top-level dirs | 3,600 tok | Monorepos, platforms, enterprise systems |

Gợi ý ghi đè trong chat — ProjectLens đọc ý định:

| Signal | Resulting tier |
|---|---|
| "quick summary" / "gist" / "tldr" | T1 |
| "onboard me" / "explain the project" / default | T2 |
| "monorepo" / "all services" / "full picture" | T3 |

---

## Phạm vi framework — 30 adapter trong 8 gói

30 adapter trên 8 gói. Mỗi adapter ~80–120 LOC, được tải lười chỉ khi chữ ký framework khớp với dự án.

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

Một lần quét ProjectLens duy nhất trên một dự án phát triển AI làm nổi bật mọi mắt xích trong chuỗi: từ notebook thô qua đào tạo, mô hình hóa, embedding, điều phối tác nhân, thành phần UI và triển khai sản xuất — tất cả trong **một viên nang**, dưới ngân sách.

---

## Hooks phiên — 5 hooks sản xuất

5 hook kết hợp trên một phiên Claude Code. Tiết kiệm token tích lũy trong suốt vòng đời của phiên.

| Hook | Event | Effect | Approximate savings |
|---|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file — agent gets a "you already saw this at turn N" hint | **~25%** on long sessions |
| `activity_hook.py` | PostToolUse:Edit \| Write \| Bash | Tracks session state; refreshes session capsule every 5 turns | Enables compactor |
| `inject_hook.py` | UserPromptSubmit | Injects only the **relevant** capsule sections per prompt (not the whole capsule) | **~60%** per-prompt savings |
| `compress_hook.py` | PostToolUse:Bash \| WebFetch | Deterministic compression of long tool outputs (HTML/JSON/log/trace/diff/pytest) | Variable, often 80%+ |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work | Carries context across `/clear` boundaries |

**Hạn chế Cowork:** chỉ SessionStart kích hoạt trong bề mặt hook của Cowork. Công cụ quét, tạo viên nang và `/projectlens compact` vẫn hoạt động — nhưng 5 tối ưu hóa do hook điều khiển chỉ kích hoạt trong CLI terminal của Claude Code.

---

## Bộ nén hội thoại

Phiên dài tiêu thụ ngữ cảnh. Bộ nén thu hồi 8-25k token trong vài giây.

```bash
/projectlens compact          # generate WORKING_CONTEXT.md
/clear                        # flush the conversation buffer
# then paste WORKING_CONTEXT.md at the top of the new session
```

Bộ nén đọc trạng thái phiên được ghi bởi `activity_hook` và tạo `WORKING_CONTEXT.md` tóm tắt:

- Files you touched (with line counts and last operation)
- Bash commands run and their outcomes
- Tests that passed / failed
- Decisions made, open threads
- Optional LLM-enhanced one-paragraph summary if `ANTHROPIC_API_KEY` is set (one Haiku call, ~$0.001)

Cảnh báo trạng thái trống: nếu không có hook PostToolUse nào kích hoạt (điển hình trong Cowork), bộ nén xuất chẩn đoán rõ ràng thay vì giả vờ đã ghi lại công việc.

---

## Kinh tế token — con số cụ thể

Tiết kiệm đến từ đâu — con số cụ thể từ sử dụng sản xuất:

| Stage | Before ProjectLens | With ProjectLens | Savings |
|---|---|---|---:|
| Initial orientation | 8,000–20,000 tokens reading 20+ files | One capsule, 800–3,300 tokens | **70–90%** |
| Repeat reads | Each re-read costs full file (≈400 tok / 100 LOC) | Dedup flag, ~0 tokens | **~25%** on long sessions |
| Per-prompt re-injection | Full capsule (2,100 tok) every prompt | Only relevant sections (~800 tok) | **~60%** |
| Long tool outputs | Raw 50 KB Bash output → 12k tokens | Compressed summary + retrieval handle | **80%+** variable |
| Mid-session compaction | `/clear` loses everything | `WORKING_CONTEXT.md` preserves continuity | **8–25k** reclaimable |

**Ví dụ chi phí (giá Opus, $15/Mtok đầu vào):** phiên lập trình 4 giờ trước đây tốn ~$3 ở token đầu vào giảm xuống ~$0.45–$0.90 với tất cả hook hoạt động.

---

## Kiểm thử và ngân sách hiệu suất

**527 unit test** + **17 ngân sách hiệu suất và bảo mật do CI áp đặt** chạy trên mỗi commit qua macOS / Linux / Windows × Python 3.9–3.12.

Hiệu suất đo được trên kích thước dự án tổng hợp:

| Project size | Files | Scan time | Capsule size | Sections rendered |
|---|---:|---:|---:|---:|
| Tiny | 20 | **41 ms** | 402 tok | 5 |
| Medium | 100 | **29 ms** | 529 tok | 5 |
| Large | 500 | **113 ms** | 529 tok | 5 |

Kích thước viên nang vẫn **bị giới hạn bởi ngân sách tầng bất kể kích thước dự án** — thời gian quét tuyến tính, đầu ra không đổi. Đó là hào kiến trúc.

Giới hạn cứng được áp đặt trong CI:

| Operation | Hard cap |
|---|---|
| Hook subprocess startup | < 250 ms |
| Scan on 100-file fixture | < 2.5 s |
| Capsule build | < 200 ms |
| Hook output envelope | ≤ 500 tokens per event |
| `SKILL.md` size | < 8 KB |
| Rule R1 — hooks framework-free | static-analysis enforced |
| Rule R3 — `detect()` never opens files | static-analysis enforced |

Thêm adapter không thể làm thoái lui bất kỳ giới hạn nào trong số này. Pull Request vi phạm ngân sách làm CI thất bại.

---

## Bảo mật và quản trị

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

**Không có gì được gửi ra ngoài thiết bị** trừ khi bạn chạy `/projectlens compact --llm` một cách rõ ràng. Tệp thống kê và bộ nhớ là JSON thuần — có thể kiểm tra, có thể xóa, không có PII.

For governance — what contributions we accept and what we don't — see [`GOVERNANCE.md`](../../GOVERNANCE.md).

---

## Biến môi trường cấu hình

Tất cả bề mặt liên tục có opt-out biến môi trường được tài liệu hóa:

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

Bỏ đặt để kích hoạt lại. Không có gì khác thay đổi — không có tệp plugin nào được di chuyển, không có dữ liệu nào bị mất.

---

## Cấu trúc dự án

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

## Mở rộng — viết adapter của riêng bạn

SDK adapter cố ý nhỏ. Mỗi adapter ~80-120 LOC.

### Write a new framework adapter

```bash
cd skills/projectlens/scripts/frameworks
cp -r _template _myframework
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes
$EDITOR manifest.json                    # register entry
$EDITOR ../../../../tests/test_myframework.py   # add tests
```

Hợp đồng mọi adapter phải tuân theo:

| Rule | What |
|---|---|
| **R1** | Hook scripts never import from `frameworks/*` (CI-enforced) |
| **R2** | Adapter modules stay small — ~80–120 LOC |
| **R3** | `detect()` is O(1) — never opens files (CI-enforced) |
| **R4** | `extract()` reads only files that match your framework's signature |
| **R5** | `capsule_section()` respects `budget_tokens` |

Full guide: [`skills/projectlens/references/adapter-sdk.md`](../../skills/projectlens/references/adapter-sdk.md).

### Per-project user adapters (no fork needed)

Đặt tệp `.py` vào `<your-project>/.projectlens/frameworks/`. Chúng được tự động phát hiện mỗi lần quét sau khi bạn opt-in:

```bash
export PROJECTLENS_USER_ADAPTERS=1
```

Quyết định tin cậy xảy ra trong shell của bạn, không phải trong mã đang được quét — bảo vệ bạn khỏi các adapter độc hại trong repo không tin cậy.

---

## So sánh với các lựa chọn thay thế

ProjectLens là **lớp định hướng nhẹ, xác định** trong không gian trợ lý lập trình AI. Nó bổ sung cho các công cụ tìm kiếm ngữ nghĩa thay vì thay thế chúng.

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
Đ: Quét cơ bản (đi qua tệp, phát hiện ngôn ngữ, ký hiệu) hoạt động trên JS, TS, Go, Java, Rust, Ruby, PHP, C/C++ và ~20 ngôn ngữ khác. 30 adapter dành riêng cho framework chủ yếu tập trung vào Python hiện tại, với Vue SFC + Tailwind + Docker Compose phủ phần JS/web. Các adapter framework JS/TS (Next.js, Astro, SvelteKit, NestJS) có trong lộ trình.

**Q: Will it slow down my Claude Code session?**
Đ: Khởi động tiến trình con hook bị giới hạn ở 250 ms lạnh (thường 20-30 ms nóng). Đầu ra hook bị giới hạn ở 500 token mỗi sự kiện. Cả hai giới hạn đều được CI áp đặt. Bản thân quét chạy theo yêu cầu, không phải mỗi prompt.

**Q: Does it send my code anywhere?**
Đ: Không, trừ khi bạn chạy `/projectlens compact --llm` một cách rõ ràng VÀ có `ANTHROPIC_API_KEY` được đặt. Ngay cả khi đó, chỉ tóm tắt hoạt động phiên (đường dẫn tệp, tên lệnh, kết quả test) được gửi — không bao giờ là nội dung tệp.

**Q: Is the capsule different from a README?**
Đ: README cho **con người** biết dự án làm gì. Viên nang cho **tác nhân** của bạn biết dự án chứa gì: route, model, vòng huấn luyện, chỉ mục vector, triển khai, v.v. Khán giả khác, đầu ra khác, cả hai đều có chỗ.

**Q: What if my framework isn't covered by an adapter?**
A: The base scan still produces a useful capsule (entry points, modules, symbols, hotspots, risks). You get less framework-specific noise. Add a custom adapter in ~100 LOC if you want richer output for that framework — see [the adapter SDK guide](../../skills/projectlens/references/adapter-sdk.md).

**Q: Can I disable everything and just use the scan?**
A: Yes — `export PROJECTLENS_DEDUP=0` disables all 5 hooks. The scan engine remains available for explicit `/projectlens` invocations.

**Q: Why not use Cursor's @codebase or Sourcegraph Cody instead?**
A: They do **semantic** vector search — they need an embedding model, a vector store, and continuous indexing. ProjectLens does **structural** extraction — deterministic, fast (sub-second), cheap, and framework-aware. The two are complementary: ProjectLens for instant orientation, semantic tools for in-depth search.

**Q: How does compaction interact with `/clear`?**
A: Run `/projectlens compact` first (generates `WORKING_CONTEXT.md`), then `/clear` to flush the conversation buffer, then paste the contents of `WORKING_CONTEXT.md` at the top of the next session. You resume with the same shoulder-context but a fresh token budget. Compaction typically reclaims 8–25k tokens.

**Q: Is it free?**
Đ: Có — giấy phép MIT. Không có đăng ký, không có telemetry off-device, không có phụ thuộc pip bắt buộc.

**Q: How do I uninstall?**
A: Plugin: drag-remove from your tool's plugin manager. MCP: remove the `projectlens` entry from your MCP config. CLI: `pip uninstall projectlens`. Data: `rm -rf ~/.projectlens` and `<project>/.projectlens-memory` to wipe everything.

---

## Lộ trình

| Pack | Status | Notes |
|---|---|---|
| `_ai_apps` v2 — LiteLLM, Instructor, AutoGen | Planned | Next AI-dev sprint |
| `_ml_core` v2 — JAX, Flax, MLX, fastai | Planned | After v2 ai_apps |
| `_serving` v2 — Modal, Replicate, Cog | Planned | |
| `_enterprise` v2 — Django, Flask, Next.js, NestJS | Planned | JS/TS framework coverage |
| Multi-modal lightweight — SQL schemas, shell scripts, Dockerfile, Markdown docs | Investigating | v0.16.0 candidate |
| Optional graph mode — `projectlens graph .` + MCP graph queries | Investigating | v0.17.0 candidate |
| `projectlens watch` daemon — auto-refresh AGENTS.md on file changes | Investigating | Cross-tool freshness |

Bỏ phiếu với GitHub issues — cái gì nên đến trước?

---

## Đóng góp và giấy phép

Chúng tôi hoan nghênh:
- New framework adapters (see [`CONTRIBUTING.md`](../../CONTRIBUTING.md))
- Bug fixes with regression tests
- Doc improvements + new integration recipes
- Performance work that keeps the perf budgets green

Chúng tôi không chấp nhận:
- `exec`, `eval`, `pickle.loads`, `shell=True`, `os.system` (CI-enforced)
- New outbound HTTP endpoints
- Telemetry or analytics sent off-device
- Adapters with hardcoded credentials or scraping behavior

See [`GOVERNANCE.md`](../../GOVERNANCE.md) for the full policy.

**License:** MIT. © Sachin Patil. See [`LICENSE`](../../LICENSE).

**Maintainer:** Sachin Patil — `agenticailab01@gmail.com`. For security reports, see [`SECURITY.md`](../../SECURITY.md).

---

⭐ Đánh dấu sao repo này nếu ProjectLens tiết kiệm token cho bạn. Mở một issue nếu framework bạn sử dụng không được phủ — hầu hết các adapter là ~100 LOC và chúng tôi sẽ ưu tiên.
