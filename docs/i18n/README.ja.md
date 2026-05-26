# Lensify

> 🌐 **日本語** — 英語版に戻る: [English](../../README.md)


[![CI](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticailab01/lensify/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE) [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Version](https://img.shields.io/badge/version-0.15.0-brightgreen.svg)](../../CHANGELOG.md) [![Tests](https://img.shields.io/badge/tests-527%20passing-brightgreen.svg)](#tests--performance) [![Adapters](https://img.shields.io/badge/adapters-30%20across%208%20packs-blue.svg)](#framework-coverage)

> **AI コーディングエージェント向けのシングルスキャン適応プロジェクトレンズ + トークン最適化コンテキストカプセル。** 方向付けトークンを 70–90% 削減。AI 開発ライフサイクル全体でフレームワーク認識。純粋な標準ライブラリ。MIT ライセンス。

**📖 あなたの言語で読む:** 🇬🇧 [← 英語版に戻る](../../README.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇹🇼 [繁體中文](README.zh-TW.md) · 🇰🇷 [한국어](README.ko.md) · 🇩🇪 [Deutsch](README.de.md) · 🇫🇷 [Français](README.fr.md) · 🇪🇸 [Español](README.es.md) · 🇮🇳 [हिन्दी](README.hi.md) · 🇧🇷 [Português](README.pt.md) · 🇷🇺 [Русский](README.ru.md) · 🇸🇦 [العربية](README.ar.md) · 🇮🇹 [Italiano](README.it.md) · 🇵🇱 [Polski](README.pl.md) · 🇳🇱 [Nederlands](README.nl.md) · 🇹🇷 [Türkçe](README.tr.md) · 🇺🇦 [Українська](README.uk.md) · 🇻🇳 [Tiếng Việt](README.vi.md) · 🇮🇩 [Bahasa Indonesia](README.id.md) · 🇸🇪 [Svenska](README.sv.md) · 🇬🇷 [Ελληνικά](README.el.md) · 🇷🇴 [Română](README.ro.md) · 🇨🇿 [Čeština](README.cs.md) · 🇫🇮 [Suomi](README.fi.md) · 🇩🇰 [Dansk](README.da.md) · 🇳🇴 [Norsk](README.no.md) · 🇭🇺 [Magyar](README.hu.md) · 🇹🇭 [ภาษาไทย](README.th.md) · 🇺🇿 [O'zbekcha](README.uz.md)

---

## 目次

1. [Lensify を選ぶ理由](#why-lensify)
2. [一目で](#at-a-glance)
3. [クイックスタート](#quick-start)
4. [仕組み](#how-it-works)
5. [ツール別インストール(4 チャネル)](#installation-by-tool)
6. [適応階層 — T1 / T2 / T3](#adaptive-tiers)
7. [フレームワークカバレッジ — 8 パックの 30 アダプター](#framework-coverage)
8. [セッションフック — 5 つの本番フック](#session-hooks)
9. [会話コンパクター](#conversation-compactor)
10. [トークン経済学 — 具体的な数字](#token-economics)
11. [テストとパフォーマンス予算](#tests--performance)
12. [セキュリティとガバナンス](#security--governance)
13. [設定環境変数](#configuration)
14. [プロジェクト構造](#project-structure)
15. [拡張 — 独自のアダプターを書く](#extending-lensify)
16. [代替手段との比較](#comparison)
17. [よくある質問](#faq)
18. [ロードマップ](#roadmap)
19. [貢献とライセンス](#contributing--license)

---

## Lensify を選ぶ理由

現代の AI コーディングエージェントにはコンテキストウィンドウの問題があります:プロジェクトが大きいほど、**自己の方向付け**だけで消費するトークンが増えます。典型的なオンボーディングでは、エージェントが有用な作業を始める前に 20~40 ファイルを読み込みます — つまり 10〜30k トークンが理解に費やされ、ユーザーの実際の問題解決には使われません。

Lensify はその方向付け段階を**シングルスキャン**(100 ms 未満)に置き換え、トークン上限付き・フレームワーク認識のコンテキストブロックを生成します。エージェントは数十のファイルではなく**1 つのカプセル**を読みます。方向付けの節約だけでトークン使用量が 70〜90% 減少し、さらに 5 つのセッションフックで追加の節約が積み重なります。

**そのトレードオフ:**セマンティックベクトル検索(より遅い、埋め込みコスト、汎用)ではなく、決定論的な構造抽出(高速、無料、フレームワーク認識)を選択します。Lensify は Cursor の `@codebase` や Sourcegraph Cody などのセマンティックツールと対立せず、共存します。即時の方向付けには Lensify を、構造ではなく意味で特定の何かを探す必要があるときはセマンティック検索を使ってください。

---

## 一目で

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

## クイックスタート

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

These are your tool's **own** documented commands — no `curl | bash`, no remote-script execution. Three new tools appear after restart: `lensify_scan`, `lensify_compact`, `lensify_stats`.

📖 完全なステップバイステップ手順は **[`USER-INSTALL.md`](../../USER-INSTALL.md)**
---

## 仕組み

スキャンエンジンは呼び出しごとに 5 つのフェーズを実行します:

| Phase | What it does | Output |
|---|---|---|
| **1. Walk** | Respects `.gitignore` + vendor exclusions. Categorises every file as code / doc / meta. | File inventory |
| **2. Parse** | Python via stdlib `ast`. JS/TS/Go/Java via regex. Captures imports + public symbols. | Per-file metadata |
| **3. Tier** | Picks T1/T2/T3 from file count, LOC, top-level dirs, monorepo markers. | Token budget |
| **4. Adapt** | Lazy-loads matching framework adapters via manifest. Each emits a typed section. | Framework records |
| **5. Render** | Composes the capsule under tier budget. Writes HTML lens. Caches the result. | Capsule + HTML |

典型的な実行時間:中規模プロジェクトで**30 ms**、500 ファイルプロジェクトで**113 ms**。スキャンはフェーズ間でファイルを再読み込みしません。

**スキャンごとに 2 つの成果物:**

1. **`LENS.html`** — single self-contained HTML page (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns). For humans — 30-second read.
2. **`LENS.capsule.md`** — Markdown context block, 800–3,600 tokens, framework-aware. For your AI agent — ingested instead of reading 30+ raw files.

---

## ツール別インストール(4 チャネル)

4 つの配布チャネルが同じスキャンエンジンを共有します。お使いのツールに合うものを選んでください。

### Channel 1 — Claude Code / Cowork plugin (recommended)

完全な体験:5 つすべてのフック発火、スラッシュコマンド、ステータスライン、メモリローダー。

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

純標準ライブラリの JSON-RPC 2.0 stdio サーバー。サーバー自体に `pip install` 手順は不要 — Python 標準ライブラリのみで、クローンしたリポジトリから直接実行できます。

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

## 適応階層 — T1 / T2 / T3

Lensify は適切な深さを自動的に選択します。`--tier T1|T2|T3` のオーバーライドは強い理由があるときだけ使ってください。

| Tier | Trigger | Capsule budget | Use case |
|---|---|---:|---|
| **T1 Sketch** | < 50 files · < 5k LOC · single language | 500 tok | Quick scripts, demos, single-file tools |
| **T2 Atlas** | 50–1,000 files · 5k–100k LOC · multi-module | 2,100 tok | Most real projects (the sweet spot) |
| **T3 Compass** | > 1,000 files · monorepo markers · 5+ top-level dirs | 3,600 tok | Monorepos, platforms, enterprise systems |

チャット内のオーバーライドヒント — Lensify は意図を読み取ります:

| Signal | Resulting tier |
|---|---|
| "quick summary" / "gist" / "tldr" | T1 |
| "onboard me" / "explain the project" / default | T2 |
| "monorepo" / "all services" / "full picture" | T3 |

---

## フレームワークカバレッジ — 8 パックの 30 アダプター

8 パックにわたる 30 のアダプター。各アダプターは約 80〜120 行のコードで、フレームワークシグネチャがプロジェクトに一致するときだけ遅延ロードされます。

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

AI 開発プロジェクトでの 1 回の Lensify スキャンで、チェーン全体のすべてのリンクが浮かび上がります:生のノートブックからトレーニング、モデリング、埋め込み、エージェント編成、UI コンポーネント、本番デプロイまで — すべて**1 つのカプセル**に、予算内で。

---

## セッションフック — 5 つの本番フック

5 つのフックは Claude Code セッション全体で複合的に作用します。トークン節約はセッションの全期間にわたって積み重なります。

| Hook | Event | Effect | Approximate savings |
|---|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file — agent gets a "you already saw this at turn N" hint | **~25%** on long sessions |
| `activity_hook.py` | PostToolUse:Edit \| Write \| Bash | Tracks session state; refreshes session capsule every 5 turns | Enables compactor |
| `inject_hook.py` | UserPromptSubmit | Injects only the **relevant** capsule sections per prompt (not the whole capsule) | **~60%** per-prompt savings |
| `compress_hook.py` | PostToolUse:Bash \| WebFetch | Deterministic compression of long tool outputs (HTML/JSON/log/trace/diff/pytest) | Variable, often 80%+ |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work | Carries context across `/clear` boundaries |

**Cowork の制限:**Cowork のフック領域では SessionStart のみが発火します。スキャンエンジン、カプセル生成、`/lensify compact` は引き続き動作します — ただし 5 つのフック駆動最適化は Claude Code のターミナル CLI でのみ有効になります。

---

## 会話コンパクター

長いセッションはコンテキストを消費します。コンパクターは数秒で 8〜25k トークンを回収します。

```bash
/lensify compact          # generate WORKING_CONTEXT.md
/clear                        # flush the conversation buffer
# then paste WORKING_CONTEXT.md at the top of the new session
```

コンパクターは `activity_hook` が記録したセッション状態を読み取り、以下をまとめた `WORKING_CONTEXT.md` を生成します:

- Files you touched (with line counts and last operation)
- Bash commands run and their outcomes
- Tests that passed / failed
- Decisions made, open threads
- Optional LLM-enhanced one-paragraph summary if `ANTHROPIC_API_KEY` is set (one Haiku call, ~$0.001)

空状態の警告:PostToolUse フックが発火しなかった場合(Cowork で典型的)、コンパクターは作業を捕捉したふりをするのではなく、明確な診断を出力します。

---

## トークン経済学 — 具体的な数字

節約の出所 — 本番使用からの具体的な数字:

| Stage | Before Lensify | With Lensify | Savings |
|---|---|---|---:|
| Initial orientation | 8,000–20,000 tokens reading 20+ files | One capsule, 800–3,300 tokens | **70–90%** |
| Repeat reads | Each re-read costs full file (≈400 tok / 100 LOC) | Dedup flag, ~0 tokens | **~25%** on long sessions |
| Per-prompt re-injection | Full capsule (2,100 tok) every prompt | Only relevant sections (~800 tok) | **~60%** |
| Long tool outputs | Raw 50 KB Bash output → 12k tokens | Compressed summary + retrieval handle | **80%+** variable |
| Mid-session compaction | `/clear` loses everything | `WORKING_CONTEXT.md` preserves continuity | **8–25k** reclaimable |

**コスト例(Opus 価格、$15/Mtok 入力):**以前は入力トークンに約 $3 かかっていた 4 時間のコーディングセッションが、全フック有効で約 $0.45〜$0.90 に下がります。

---

## テストとパフォーマンス予算

**527 単体テスト** + **17 の CI 強制パフォーマンス & セキュリティ予算**がコミットごとに macOS / Linux / Windows × Python 3.9〜3.12 で実行されます。

合成プロジェクトサイズで測定したパフォーマンス:

| Project size | Files | Scan time | Capsule size | Sections rendered |
|---|---:|---:|---:|---:|
| Tiny | 20 | **41 ms** | 402 tok | 5 |
| Medium | 100 | **29 ms** | 529 tok | 5 |
| Large | 500 | **113 ms** | 529 tok | 5 |

カプセルサイズはプロジェクトサイズに関係なく**階層予算内に制限**されます — 線形なスキャン時間、一定の出力。これがアーキテクチャの堀です。

CI で強制される上限:

| Operation | Hard cap |
|---|---|
| Hook subprocess startup | < 250 ms |
| Scan on 100-file fixture | < 2.5 s |
| Capsule build | < 200 ms |
| Hook output envelope | ≤ 500 tokens per event |
| `SKILL.md` size | < 8 KB |
| Rule R1 — hooks framework-free | static-analysis enforced |
| Rule R3 — `detect()` never opens files | static-analysis enforced |

アダプターを追加してもこれらを後退させることはできません。予算違反のプルリクエストは CI で失敗します。

---

## セキュリティとガバナンス

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

**デバイス外には何も送信されません**(明示的に `/lensify compact --llm` を実行しない限り)。統計とメモリファイルはプレーン JSON — 監査可能、削除可能、PII なし。

For governance — what contributions we accept and what we don't — see [`GOVERNANCE.md`](../../GOVERNANCE.md).

---

## 設定環境変数

すべての永続的な表面に、ドキュメント化された環境変数オプトアウトがあります:

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

再有効化するには設定解除します。それ以外何も変わりません — プラグインファイルは移動されず、データも失われません。

---

## プロジェクト構造

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

## 拡張 — 独自のアダプターを書く

アダプター SDK は意図的に小さくなっています。各アダプターは約 80〜120 行のコードです。

### Write a new framework adapter

```bash
cd skills/lensify/scripts/frameworks
cp -r _template _myframework
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes
$EDITOR manifest.json                    # register entry
$EDITOR ../../../../tests/test_myframework.py   # add tests
```

すべてのアダプターが従う必要のあるコントラクト:

| Rule | What |
|---|---|
| **R1** | Hook scripts never import from `frameworks/*` (CI-enforced) |
| **R2** | Adapter modules stay small — ~80–120 LOC |
| **R3** | `detect()` is O(1) — never opens files (CI-enforced) |
| **R4** | `extract()` reads only files that match your framework's signature |
| **R5** | `capsule_section()` respects `budget_tokens` |

Full guide: [`skills/lensify/references/adapter-sdk.md`](../../skills/lensify/references/adapter-sdk.md).

### Per-project user adapters (no fork needed)

`<your-project>/.lensify/frameworks/` に `.py` ファイルをドロップします。オプトインすれば、スキャンごとに自動検出されます:

```bash
export LENSIFY_USER_ADAPTERS=1
```

信頼の決定はスキャン対象のコードではなく、あなたのシェル内で行われます — 信頼できないリポジトリの悪意あるアダプターから保護します。

---

## 代替手段との比較

Lensify は AI コーディングアシスタント空間における**軽量で決定論的な方向付けレイヤー**です。セマンティック検索ツールを置き換えるのではなく補完します。

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

## よくある質問

**Q: Does it work on my JS/TS / Go / Rust project?**
A: 基本スキャン(ファイルウォーク、言語検出、シンボル)は JS、TS、Go、Java、Rust、Ruby、PHP、C/C++ など約 20 言語で機能します。30 のフレームワーク固有アダプターは現在主に Python に焦点を当てており、Vue SFC + Tailwind + Docker Compose が JS/Web 側をカバーしています。JS/TS フレームワークアダプター(Next.js、Astro、SvelteKit、NestJS)はロードマップにあります。

**Q: Will it slow down my Claude Code session?**
A: フックサブプロセス起動はコールド時 250 ms(通常ウォーム時 20〜30 ms)に上限設定されています。フック出力はイベントあたり 500 トークンに上限設定。両方の上限は CI で強制されます。スキャン自体はオンデマンドで実行され、プロンプトごとではありません。

**Q: Does it send my code anywhere?**
A: いいえ、明示的に `/lensify compact --llm` を実行し、**かつ** `ANTHROPIC_API_KEY` が設定されている場合を除いて送信されません。その場合でも、セッションアクティビティの要約(ファイルパス、コマンド名、テスト結果)のみが送信され、ファイル内容は決して送信されません。

**Q: Is the capsule different from a README?**
A: README は**人間**にプロジェクトが何をするかを伝えます。カプセルはあなたの**エージェント**にプロジェクトが何を含んでいるかを伝えます:ルート、モデル、トレーニングループ、ベクトルインデックス、デプロイなど。異なる対象、異なる出力、両方それぞれに役割があります。

**Q: What if my framework isn't covered by an adapter?**
A: The base scan still produces a useful capsule (entry points, modules, symbols, hotspots, risks). You get less framework-specific noise. Add a custom adapter in ~100 LOC if you want richer output for that framework — see [the adapter SDK guide](../../skills/lensify/references/adapter-sdk.md).

**Q: Can I disable everything and just use the scan?**
A: Yes — `export LENSIFY_DEDUP=0` disables all 5 hooks. The scan engine remains available for explicit `/lensify` invocations.

**Q: Why not use Cursor's @codebase or Sourcegraph Cody instead?**
A: They do **semantic** vector search — they need an embedding model, a vector store, and continuous indexing. Lensify does **structural** extraction — deterministic, fast (sub-second), cheap, and framework-aware. The two are complementary: Lensify for instant orientation, semantic tools for in-depth search.

**Q: How does compaction interact with `/clear`?**
A: Run `/lensify compact` first (generates `WORKING_CONTEXT.md`), then `/clear` to flush the conversation buffer, then paste the contents of `WORKING_CONTEXT.md` at the top of the next session. You resume with the same shoulder-context but a fresh token budget. Compaction typically reclaims 8–25k tokens.

**Q: Is it free?**
A: はい — MIT ライセンス。サブスクリプションなし、デバイス外テレメトリーなし、必須の pip 依存関係なし。

**Q: How do I uninstall?**
A: Plugin: drag-remove from your tool's plugin manager. MCP: remove the `lensify` entry from your MCP config. CLI: `pip uninstall lensify`. Data: `rm -rf ~/.lensify` and `<project>/.lensify-memory` to wipe everything.

---

## ロードマップ

| Pack | Status | Notes |
|---|---|---|
| `_ai_apps` v2 — LiteLLM, Instructor, AutoGen | Planned | Next AI-dev sprint |
| `_ml_core` v2 — JAX, Flax, MLX, fastai | Planned | After v2 ai_apps |
| `_serving` v2 — Modal, Replicate, Cog | Planned | |
| `_enterprise` v2 — Django, Flask, Next.js, NestJS | Planned | JS/TS framework coverage |
| Multi-modal lightweight — SQL schemas, shell scripts, Dockerfile, Markdown docs | Investigating | v0.16.0 candidate |
| Optional graph mode — `lensify graph .` + MCP graph queries | Investigating | v0.17.0 candidate |
| `lensify watch` daemon — auto-refresh AGENTS.md on file changes | Investigating | Cross-tool freshness |

GitHub Issues で投票 — 何を優先すべきですか?

---

## 貢献とライセンス

歓迎するもの:
- New framework adapters (see [`CONTRIBUTING.md`](../../CONTRIBUTING.md))
- Bug fixes with regression tests
- Doc improvements + new integration recipes
- Performance work that keeps the perf budgets green

受け入れないもの:
- `exec`, `eval`, `pickle.loads`, `shell=True`, `os.system` (CI-enforced)
- New outbound HTTP endpoints
- Telemetry or analytics sent off-device
- Adapters with hardcoded credentials or scraping behavior

See [`GOVERNANCE.md`](../../GOVERNANCE.md) for the full policy.

**License:** MIT. © Sachin Patil. See [`LICENSE`](../../LICENSE).

**Maintainer:** Sachin Patil — `agenticailab01@gmail.com`. For security reports, see [`SECURITY.md`](../../SECURITY.md).

---

⭐ Lensify がトークンを節約したら、このリポジトリにスターを付けてください。使用しているフレームワークがカバーされていない場合は、Issue を開いてください — 大半のアダプターは約 100 行のコードで、優先します。
