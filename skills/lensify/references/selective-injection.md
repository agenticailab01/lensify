# Selective Capsule Injection (Phase 3)

The v0 capsule was monolithic — the whole thing sat in `CLAUDE.md`. Phase 3
splits the capsule into addressable sections and injects only the ones
relevant to each user prompt.

## How it works

1. `scan.py` writes `lensify-out/lens.sections.json` alongside the
   capsule. Each capsule section (SUMMARY, ENTRY, MODULES, CONVENTIONS,
   HOTSPOTS, RISKS) becomes an addressable JSON key.
2. The `UserPromptSubmit` hook (`inject_hook.py`) fires when the user
   submits a prompt.
3. `section_matcher.py` scores each section against the prompt using
   keyword and module-name matching. It picks 1–4 winners.
4. The hook reads only those section bodies and returns them as
   `additionalContext`.
5. If the user is asking about session activity (e.g. "what have we done?"),
   `SESSION.capsule.md` is appended too.

## Section keywords (illustrative — see `section_matcher.py` for the full list)

| Section | Trigger phrases |
|---|---|
| `summary` | "what is this", "overview", "purpose", "tl;dr" |
| `entry` | "run", "start", "execute", "deploy", "command" |
| `modules` | "where", "live", "find", "module", "structure" |
| `conventions` | "style", "lint", "format", "convention", "pattern" |
| `hotspots` | "active", "churn", "hot", "recent changes" |
| `risks` | "risk", "broken", "issue", "concern" |

Plus: any **known module name** from `module_paths` (e.g., "auth", "api")
boosts MODULES by +3 score.

## Selection rules

- Sections with score > 0 are returned, highest score first
- Hard cap: **4 sections per prompt** (configurable via `MAX_SECTIONS`)
- If NO section scored, the matcher falls back to `summary + modules` as a
  safe default (most generally useful pair)
- Empty / very short prompts (< 3 chars) get nothing

## Why this saves tokens

A monolithic capsule of ~1,500 tokens is re-included in every prompt's
context. With selective injection, the average prompt gets ~400 tokens of
*relevant* sections instead. Across an 8-turn session that's a ~9,000 token
saving on top of the v0 lens savings.

## Failure modes (and their fallbacks)

| Failure | Fallback |
|---|---|
| `lens.sections.json` missing | Hook emits empty; agent works without lens |
| Sections file malformed | Hook emits empty; logged to stderr |
| No keyword/module matches | Safe default: SUMMARY + MODULES |
| User on a platform without hooks | Static capsule still works via CLAUDE.md |

## What's deliberately NOT done

- **No embeddings**: deterministic rule-based matching is fast (<5ms),
  predictable, and debugger-friendly. Embeddings would be more accurate but
  add a dependency, a per-call cost, and unexplainable misses.
- **No history-aware ranking**: the matcher treats each prompt independently.
  In a future Phase, the session state could bias scores toward sections
  related to recent activity.

## Inspecting decisions

Run the matcher standalone to see what it would pick:

```bash
python3 -c "from section_matcher import match; \
  r = match('where does auth live?', module_paths=['auth','api','db']); \
  print('sections:', r.sections); \
  print('scores:', r.scores); \
  print('matched modules:', r.matched_modules)"
```
