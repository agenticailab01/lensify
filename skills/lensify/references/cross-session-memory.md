# Cross-Session Memory Bridge (Phase 7)

Lensify v0.5.0 adds project-local persistent memory: each time the user
runs `/lensify compact`, the WORKING_CONTEXT.md is *also* saved as a
memory entry. At the start of every new session in the same project, the top
3 most-relevant past memories are auto-injected as additionalContext.

This closes the gap with Claude-Mem — without the MCP server, the SQLite
database, or the vector store. The trade-off is simplicity vs accuracy:
Claude-Mem uses Chroma embeddings (95.2% recall on LongMemEval); Lensify
uses recency × module-overlap scoring (no exact benchmark, but adequate for
the use cases we care about — "what was I doing in this repo last week?").

## Storage layout

```
<project-root>/.lensify-memory/
    index.json                       # catalog of all memories, sorted by recency
    memory-<safe_session_id>.json    # one file per past session
```

Files are auto-pruned at MAX_MEMORIES=50; oldest drop first.

## Memory entry contents

Each memory captures:

- Session metadata (id, started_at, last_turn, duration_minutes)
- Top-5 active modules (by activity score from session_state)
- Last 10 files touched
- Last test result summary
- 400-char excerpt from WORKING_CONTEXT.md
- Auto-extracted topics (frequent meaningful words from edits + commands)

A typical memory entry is ~1.5 KB on disk. With MAX_MEMORIES=50 the total
storage footprint is ~75 KB.

## Retrieval scoring

When a new session opens, `memory_loader.py` runs and scores every memory:

```
score = recency_decay × 0.5 + module_overlap × 1.0

where:
    recency_decay = 0.5 ^ (age_days / 14)
    module_overlap = |current_top_modules ∩ memory_modules| / |current_top_modules|
```

The recency half-life is 14 days. Module overlap dominates the signal —
recent work on the same module surfaces strongly; old work elsewhere fades.

Top-K=3 memories with positive score are formatted as a single
`additionalContext` block.

## Injected block format

What the agent sees at SessionStart:

```
[Lensify] Memories from previous sessions in this project:

### Memory 1 — 3 hours ago, turn 14, ~52 min
- Active modules: `api/`, `domain/`, `tests/`
- Files touched: `api/auth.py`, `domain/user.py`, `tests/test_auth.py`
- Last test: pytest: 2 failed, 28 passed
- Topics: authentication, jwt, refresh, middleware, expiry
- Excerpt: Iterating on JWT refresh flow. Auth middleware now rejects
  expired tokens but the refresh endpoint has a race condition under
  concurrent requests…

### Memory 2 — 2 day(s) ago, turn 9, ~31 min
- Active modules: `api/`, `domain/`
- ...

These are advisory hints — re-read files as needed, but consider this prior
context when answering.
```

## How memories get created

A memory is written whenever `compact.py` is run (manually via
`/lensify compact` or by the skill flow). The compactor:

1. Builds WORKING_CONTEXT.md as usual.
2. Constructs a MemoryEntry from the session state.
3. Calls `save_memory()` to persist it and update the index.

If the user never runs `/lensify compact`, no memories accumulate. This
is intentional: memories should reflect deliberate session-end snapshots, not
every transient state.

## Privacy + safety

- All memory data is project-local (lives in the project directory).
- No data leaves your machine.
- Opt out: `LENSIFY_MEMORY=0`.
- Wipe: `rm -rf .lensify-memory/`.
- Recommended `.gitignore` entry: `.lensify-memory/` (default-private).
  Teams that *want* shared memory can commit it intentionally.

## Trade-offs vs Claude-Mem

| Property | Lensify memory | Claude-Mem |
|---|---|---|
| Install footprint | 0 extra files | MCP server + SQLite + Chroma |
| External dependencies | none | chromadb, mcp, etc. |
| Scoring | recency × module-overlap | vector similarity |
| Recall accuracy | adequate for project-scoped queries | 95.2% on LongMemEval |
| Cross-tool sharing | project-local only | global, cross-tool |
| Setup time | zero (auto-installed with plugin) | a few minutes |
| Maintenance | none | runs an HTTP worker on port 37777 |

For users with simple project-scoped needs (the common case for DEWA
developers), Lensify memory is enough. For users with cross-project,
high-recall needs (the common case for full-time AI engineers), Claude-Mem
remains better — and Lensify deliberately doesn't compete on that axis.

The two stack: if you have Claude-Mem installed, Lensify memory still
runs and doesn't conflict. You get project-scoped + global memory.

## What's NOT done in v0.5.0

- Embedding-based retrieval (deferred to Phase 7.1; would require optional
  numpy or a tiny in-house BM25)
- Cross-project memory (deliberately out of scope; Claude-Mem does this)
- LLM-summarized memory excerpts (deterministic excerpt of WORKING_CONTEXT)
- UI for browsing / editing past memories (CLI listing only via the index file)
