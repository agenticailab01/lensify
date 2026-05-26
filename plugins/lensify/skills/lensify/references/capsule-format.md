# Capsule Format

The capsule is the token-saving payload. It is the artefact agents read *instead of* the raw codebase. Format is fixed Markdown so any agent can ingest it.

## Section order (priority — bottom truncated first)

1. **`# SUMMARY`** — one sentence. Always present. Never truncated.
2. **`## ENTRY`** — entry points: bin scripts, main modules, server bootstrap files. One bullet each, with relative path.
3. **`## MODULES`** — directory → purpose mapping. One row per top-level module.
4. **`## CONVENTIONS`** — extracted from the project's own conventions (lint configs, README, contributing guide).
5. **`## HOTSPOTS`** — top files by git churn (last 90 days). Truncated before MODULES.
6. **`## RISKS`** — confidence-tagged anomalies (cyclical imports, dead modules, untested hot paths). Truncated first.

## Token budgets

| Tier | Total tokens | Per-section soft cap |
|---|---|---|
| T1 | 500 | SUMMARY=30, ENTRY=80, MODULES=200, CONVENTIONS=80, HOTSPOTS=70, RISKS=40 |
| T2 | 1,500 | SUMMARY=40, ENTRY=150, MODULES=600, CONVENTIONS=250, HOTSPOTS=300, RISKS=160 |
| T3 | 2,500 | SUMMARY=60, ENTRY=300, MODULES=1,000, CONVENTIONS=400, HOTSPOTS=500, RISKS=240 |

Token counting uses a fast 4-chars-per-token approximation; exact counts come from `tiktoken` when available (optional dependency).

## Example (T2 capsule)

```markdown
<!-- lensify-begin -->
# SUMMARY

REST API in Python + FastAPI managing hospital inventory; PostgreSQL persistence; 312 files, 41k LOC.

## ENTRY

- `app/main.py` — FastAPI app factory and route registration
- `app/cli.py` — admin CLI (seed, migrate, healthcheck)
- `worker/run.py` — background job worker

## MODULES

| Path | Purpose |
|---|---|
| `app/api/` | HTTP route handlers, request validation |
| `app/domain/` | Business logic, pure functions, no I/O |
| `app/db/` | SQLAlchemy models and repository pattern |
| `app/auth/` | JWT auth, role-based access |
| `worker/` | Celery tasks for stock reconciliation |
| `tests/` | pytest, 78% line coverage |

## CONVENTIONS

- Black + Ruff for formatting; 100-char line length
- Type hints required on public functions (mypy strict)
- Repository pattern: domain never imports `app.db.*` directly
- API responses always wrapped in `app.api.envelope.Response`
- Test files mirror source layout under `tests/`

## HOTSPOTS

| File | Churn (90d) | Why it matters |
|---|---|---|
| `app/api/stock.py` | 47 commits | Core stock endpoints, frequent feature work |
| `app/domain/reconciliation.py` | 31 commits | INFERRED — business rules in flux |
| `app/db/models/item.py` | 22 commits | Schema migrations cluster here |
| `worker/tasks/sync.py` | 18 commits | AMBIGUOUS — could be flaky |
| `tests/test_stock_api.py` | 17 commits | Test churn tracks `stock.py` |

## RISKS

- `app/domain/reconciliation.py` has no tests (EXTRACTED — no matching test file)
- Two modules import each other: `app.api.stock` ↔ `app.domain.reconciliation` (EXTRACTED — cyclical)
- `worker/legacy/` last touched 14 months ago (INFERRED — possibly dead code)
<!-- lensify-end -->
```

## Why these sections, in this order

- **SUMMARY first** because it's the agent's anchor — if the agent only reads the first line, it should still know what this repo is.
- **ENTRY second** because "where do I run this?" is the most common first question.
- **MODULES third** because it answers "where does X live?" — the next-most-common.
- **CONVENTIONS** is what makes an agent write code that fits the project. Skip and the agent writes generic code.
- **HOTSPOTS** is "where are the bugs likely?" — change frequency is the best free signal we have.
- **RISKS** last because it's where confidence is weakest — and it's truncated first if budget is tight.

## What goes in `<!-- lensify-begin -->` markers

Always wrap the capsule in HTML comment markers so it can be cleanly removed/replaced in `CLAUDE.md`. The skill's diff mode replaces the block atomically.
