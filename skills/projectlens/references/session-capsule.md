# Session Capsule (Phase 2)

A dynamic, automatically-refreshed companion to `LENS.capsule.md`. Where the
main capsule describes the *project*, the session capsule describes *what the
agent has been doing in this chat*.

## When it refreshes

The PostToolUse hook (`activity_hook.py`) checks `should_refresh()` after
every Edit / Write / Bash call. The default rule:

- At least 3 reads have been recorded in the session
- Current turn is a multiple of 5

When both are true, a refreshed `SESSION.capsule.md` is written to
`projectlens-out/`.

## What it contains

Six sections, in priority order (truncated from the bottom when over budget):

1. **Header** — turn number, files seen, duplicates avoided
2. **Active modules** — top-N modules ranked by recent edit + read activity
3. **Recent edits** — files modified and how many times
4. **Last test run** — pytest / jest / go test detection
5. **Recently consulted files** — top reads with dedup counts
6. **Recent bash commands** — last 6 commands with exit status

Token budget: **≤ 600 tokens**.

## Example output

```markdown
<!-- projectlens-session-begin -->

# SESSION ACTIVITY

Turn 10 · 14 files seen · 24 read attempts · 10 duplicates avoided

## Active modules
- `api/` (score 480)
- `domain/` (score 210)
- `tests/` (score 90)

## Recent edits
- `api/routes.py` — edit, 3× (last turn 9)
- `api/middleware.py` — edit, 2× (last turn 7)
- `domain/auth.py` — write, 1× (last turn 8)

## Last test run

pytest: **2 failed**, 5 passed (turn 9)

- tests/test_auth.py::test_jwt_expiry
- tests/test_auth.py::test_refresh

## Recently consulted files
- `domain/auth.py` — first turn 2, 4× (dedup'd 3)
- `api/routes.py` — first turn 1, 3× (dedup'd 2)

## Recent bash commands
- `git status` ✓
- `pytest -q` ✗ (exit 1)
- `pytest tests/test_auth.py -v` ✗ (exit 1)

<!-- projectlens-session-end -->
```

## How the agent uses it

The session capsule is **not** auto-injected. It's referenced when the user
or another hook explicitly needs current-session context — typically via the
inject_hook when the user's prompt indicates session intent ("what have we
done so far", "what files have we touched").

## Why these are the right signals

- **Edits** are the strongest signal of intent — what the agent has *changed*
  tells us what's on the user's mind right now.
- **Test results** anchor the agent in reality — if tests are failing, every
  subsequent prompt likely relates to those failures.
- **Bash history** captures the side-channel work the agent does (linting,
  formatting, git, running scripts).
- **Active modules** is the join — which parts of the codebase are "hot" in
  this session, regardless of static churn.

## What is NOT tracked

- The content of file edits (diffs) — too expensive, too noisy
- The agent's reasoning trace — opaque to hooks
- Cross-session activity — that's Phase 5 (cavemem-style memory)
- Tool calls other than Read/Edit/Write/NotebookEdit/Bash

## Opt out

Same env var as the dedup feature:

```bash
export PROJECTLENS_DEDUP=0   # disables ALL projectlens hooks
```
