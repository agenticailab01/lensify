# ProjectLens

> Single-scan adaptive project lens + token-optimized context capsule for AI agents. Cuts orientation tokens by 70-90%, framework-aware across the full AI-dev lifecycle.

A Claude Code / Cowork plugin that turns any codebase into:

1. **`LENS.html`** — a one-page summary a human reads in 30 seconds (five panels: what this is, the picture, day-1 narrative, hotspots, risks & unknowns).
2. **`LENS.capsule.md`** — an 800–3,600 token context block your AI agent ingests *instead of* reading dozens of raw files.
3. **30 framework adapters across 8 packs** — surface the structural skeleton of every major AI/ML/web framework without forcing the agent to read raw code.
4. **5 production hooks** — read dedup, activity tracking, selective injection, output compression, cross-session memory — all working invisibly to reclaim tokens during long sessions.

## Quick start

```bash
# Install the plugin in Claude Code or Cowork
# (drop projectlens.plugin into the install prompt)

# Then in any project:
/projectlens                  # one-time scan → lens.html + capsule.md
/projectlens compact          # mid-session → WORKING_CONTEXT.md (reclaim 8-25k tokens)
/projectlens stats            # lifetime savings report
```

ProjectLens auto-picks a tier (T1 Sketch / T2 Atlas / T3 Compass) based on project size and complexity, so a 12-file script and a 4,000-file monorepo each get the right depth — but the user reads exactly **one page** either way.

## Framework coverage (30 adapters across 8 packs)

| Pack | Adapters | Lifecycle stage |
|---|---|---|
| `_notebooks` | Jupyter | Exploration |
| `_ml_core` | PyTorch · Transformers · scikit-learn · HF Datasets | Modeling + training |
| `_experiment` | W&B · MLflow · Comet | Tracking + observability |
| `_vector_db` | Pinecone · Weaviate · Qdrant · Chroma | Embedding stores |
| `_ai_apps` | LangChain · LlamaIndex · LangGraph · Pydantic AI · DSPy | RAG + agentic |
| `_ai_uis` | Streamlit · Gradio · Chainlit | LLM frontends |
| `_serving` | vLLM · Triton · BentoML · Ray Serve | Production inference |
| `_enterprise` | FastAPI · SQLAlchemy · Pydantic · Vue SFC · Tailwind · Docker Compose | Full-stack backend |

A single scan surfaces every link in the chain from raw notebooks through to production deployments and the experiment tracker watching them.

## What you get per scan

For each detected framework, the capsule renders a focused section. Examples:

```
## TRANSFORMERS
- model `tok` — AutoTokenizer ← `distilbert-base-uncased`  (train.py:14)
- model `model` — AutoModelForSequenceClassification ← `distilbert-base-uncased`  (train.py:15)
- trainer `trainer` — Trainer  (train.py:18)

## VLLM
- engine `llm` — LLM ← `meta-llama/Llama-3-8b-Instruct`  (serve.py:5)
- OpenAI-compatible server in: serve.py

## SQLALCHEMY
- model `User` — class User(Base) → table users · 3 cols  (models.py:6)
- model `Post` — class Post(Base) → table posts · 4 cols  (models.py:13)
- engine `engine` — create_engine(postgresql://***@localhost/db)  (models.py:22)
- relationships: User→Post, Post→User

## DOCKER-COMPOSE
- service `api` — build ./backend  (docker-compose.yml)
  - ports: 8000:8000
  - depends_on: db, redis
- service `db` — postgres:15-alpine  (docker-compose.yml)
```

Confidence-tagged: `EXTRACTED` (clean regex match), `INFERRED` (heuristic), `AMBIGUOUS` (partial).

## Hooks at work (Claude Code, full activation)

| Hook | Event | Effect |
|---|---|---|
| `dedup_hook.py` | PreToolUse:Read | Flags repeated reads of same file (~25% token savings on long sessions) |
| `activity_hook.py` | PostToolUse:Edit\|Write\|Bash | Tracks session state; refreshes session capsule every 5 turns |
| `inject_hook.py` | UserPromptSubmit | Injects only the relevant capsule sections per prompt (~60% token savings) |
| `compress_hook.py` | PostToolUse:Bash\|WebFetch | Deterministic compression of HTML/JSON/log/trace outputs |
| `memory_loader.py` | SessionStart | Loads cross-session memory of overlapping work |

Cowork runs SessionStart only — full hook activation requires Claude Code.

## Token economics

| Stage | Before ProjectLens | After ProjectLens |
|---|---|---|
| Orientation | 8,000-20,000 tokens reading 20+ files | One capsule, 800-3,300 tokens |
| Repeat reads | Each re-read costs full file | Dedup flag, ~0 tokens |
| Per-prompt re-injection | Full capsule every prompt | Only relevant sections |
| Mid-session compaction | Manual `/clear` loses everything | WORKING_CONTEXT.md preserves continuity |

**Net effect:** 70-90% of orientation tokens cut, ~25% of long-session repeat-read tokens cut, ~60% of per-prompt capsule re-injection cut, plus 8-25k reclaimable per `/projectlens compact`.

## Performance budgets (CI-enforced)

| Operation | Hard cap |
|---|---|
| Hook subprocess startup | < 250 ms |
| Scan on 100-file fixture | < 2.5 s |
| Capsule build | < 200 ms |
| Hook output envelope | ≤ 500 tokens |
| `SKILL.md` size | < 8 KB |
| Rule R1: hooks framework-free | static-analysis enforced |
| Rule R3: `detect()` never opens files | static-analysis enforced |

14 perf budgets locked in the test suite. Adding adapters can't regress these.

## Extend it — write your own adapter

ProjectLens is built on a small, documented adapter SDK. Each adapter is ~80-120 LOC.

```bash
cd skills/projectlens/scripts/frameworks
cp -r _template _myframework
mv _myframework/template.py _myframework/myframework.py
$EDITOR _myframework/myframework.py     # rename class, update regexes
$EDITOR manifest.json                    # register entry
```

See `skills/projectlens/references/adapter-sdk.md` for the full contract, design tips, and troubleshooting. The `_template/` directory contains a working reference adapter with all sections annotated.

You can also drop user-defined adapters in `<your-project>/.projectlens/frameworks/` — they get loaded automatically per-scan without needing to fork the plugin.

## Project structure

```
projectlens/
├── .claude-plugin/plugin.json          # Cowork/Claude Code manifest
├── hooks/hooks.json                    # Hook registrations
├── skills/projectlens/
│   ├── SKILL.md                        # Skill definition (lean)
│   ├── references/                     # Detailed docs (lazy-loaded)
│   │   ├── adapter-sdk.md              # Contributor guide
│   │   ├── capsule-format.md
│   │   ├── conversation-compactor.md
│   │   └── … (12 reference docs)
│   └── scripts/
│       ├── scan.py                     # Main entry point
│       ├── frameworks/                 # 30 adapters across 8 packs
│       │   ├── _template/              # SDK starter
│       │   ├── _ai_apps/
│       │   ├── _ai_uis/
│       │   ├── _ml_core/
│       │   ├── _serving/
│       │   ├── _vector_db/
│       │   ├── _experiment/
│       │   ├── _enterprise/
│       │   └── _notebooks/
│       ├── dedup_hook.py               # PreToolUse:Read
│       ├── activity_hook.py            # PostToolUse:Edit|Write|Bash
│       ├── inject_hook.py              # UserPromptSubmit
│       ├── compress_hook.py            # PostToolUse:Bash|WebFetch
│       ├── memory_loader.py            # SessionStart
│       └── statusline.py
├── CHANGELOG.md                        # v0.1 → v0.14 release notes
├── pyproject.toml
└── README.md                           # this file
```

## License

MIT. © Sachin Patil. Built by Sachin Patil.
