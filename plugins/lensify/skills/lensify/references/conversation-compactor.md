# Conversation Compactor (Phase 4)

The compactor is the biggest single token-reclaim lever in Lensify.
Where the earlier phases save tokens *as they accumulate*, the compactor
*reclaims* tokens that have already accumulated in the conversation buffer.

## When to use it

Trigger words from the user:

- "compact this conversation"
- "summarize what we've done"
- "I want to /clear but keep what we have"
- "before we /clear, save the state"
- "we're running out of context"
- "session is too long"

Conservative threshold: once a session has > 8 user turns, the compactor's
output already typically reclaims more tokens than it costs to produce.

## What it produces

`lensify-out/WORKING_CONTEXT.md` — typically 600-1,500 tokens — containing:

1. Session overview (turn count, duration, dedup stats)
2. Optional LLM-generated narrative (only with `--llm` flag)
3. Active modules (top-N by activity score)
4. Files touched (paths, ops, counts, last-touched turn)
5. Last test run (pytest/jest/go) with failing test names
6. Recent commands
7. Files consulted (with dedup counts)
8. "How to use this file" footer

The user is meant to:
1. Read the file (or scan it briefly)
2. Run `/clear` in their Claude Code session
3. Start the new session by pasting `WORKING_CONTEXT.md` content as the first
   message — Claude resumes with full context awareness but a fresh buffer

## Two modes

### Deterministic (default)

No API calls. Builds the file entirely from `.lensify-session.json`. Free,
fast (<100ms), always works.

The deterministic output covers the facts: what was edited, what was tested,
what modules are active, what's in the recent bash history. What it *can't*
tell you is the agent's reasoning — only what's observable.

### LLM-enhanced (`--llm` or env `LENSIFY_COMPACT_LLM=1`)

Adds one Haiku call (~500 input tokens, ~400 output tokens). Cost: ~$0.002
per invocation. The call adds three things on top of the deterministic
output:

- One paragraph plain-English narrative of "what we were doing"
- Inferred decisions / state-of-play (3 bullets)
- Suggested next step (1 sentence)

The narrative requires `ANTHROPIC_API_KEY` to be set. If the env var is
missing the LLM enhancement is gracefully skipped and the deterministic
file is written with a note explaining why.

## Token math — why this works

Take a session that has run for 10 user turns. Approximate per-turn cost:

| Component | Tokens |
|---|---|
| User prompt | ~150 |
| Assistant thinking + response | ~800 |
| Tool calls + results | ~850 |
| **Per-turn subtotal** | **~1,800** |

After 10 turns, the buffer carries ~18,000 tokens of history that re-loads
into every subsequent prompt. The compactor's WORKING_CONTEXT.md is
~1,000 tokens. The user pastes it into a fresh session — buffer drops from
18,000 to ~1,000 tokens. **~17,000 tokens reclaimed**.

The reclaim is *one-shot* — it's the savings at the moment of compaction.
If the new session also runs 10 turns, you've done two sessions for the
context budget of one.

At Claude Opus list price ($15/M input), 17,000 tokens reclaimed = ~$0.26
per compaction. The Haiku call costs ~$0.002. Net savings: ~$0.25 per
compaction, plus the user can continue working past the original limit.

## Safety

The compactor is read-only with respect to:
- The conversation buffer (never modified)
- CLAUDE.md (never modified)
- The session state file (only reads it)

The user is always the one who decides to /clear. The compactor never
auto-clears anything.

## What's deliberately NOT done

- **No auto-compaction**: Claude Code's built-in auto-compaction is reactive
  and lossy. The lensify compactor is on-demand and lossless within its
  observed-activity scope.
- **No transcript parsing**: parsing the raw conversation transcript would
  yield richer summaries but requires reading huge log files, makes the tool
  brittle across Claude Code versions, and the gain over `session_state` is
  marginal for the cost.
- **No multi-session merge**: each compaction is independent. Cross-session
  memory is Phase 5 / out-of-scope here.

## Inspecting the result

```bash
# Run the compactor
python3 compact.py /path/to/project

# Open the result
cat /path/to/project/lensify-out/WORKING_CONTEXT.md
```

The banner JSON on stdout contains the reclaim estimate so the calling skill
can report numbers back to the user:

```json
{
  "path": ".../WORKING_CONTEXT.md",
  "tokens_reclaimed_est": 17400,
  "llm_enhanced": false
}
```
