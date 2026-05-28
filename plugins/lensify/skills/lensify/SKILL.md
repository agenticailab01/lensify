---
name: lensify
description: Produce a single-page adaptive project lens and token-optimized context capsule for any codebase. Use when the user asks to understand a project, scan a repo, summarize a codebase, onboard onto a project, build a project map, generate a context capsule, or save tokens on a repo. Auto-adapts depth based on project size and complexity.
---

# Lensify

Generate a one-page adaptive project lens plus a token-optimized context capsule.

## When to invoke

- Understand a codebase quickly (their own, a vendor's, a legacy handover)
- Onboard a new joiner
- Reduce token usage by giving the agent pre-baked context
- Produce a single-page artefact for non-technical reviewers
- Compare projects structurally (`--diff`)
- Compact a long conversation (`compact`)
- Show lifetime savings (`stats`)

## What to produce

Two artefacts in `lensify-out/`:

1. `LENS.html` — single self-contained HTML page (five panels: What this is, The picture, Day-1 narrative, Hotspots, Risks & unknowns).
2. `LENS.capsule.md` — 800–2,500 token Markdown block that drops into `CLAUDE.md` / `AGENTS.md`.

Plus `lens.json`, `lens.sections.json`, and `manifest.json` inside `lensify-out/`.

## How to do it

Call the bundled scan engine:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lensify/scripts/scan.py <target-path> [flags]
```

Flags: `--tier T1|T2|T3|auto`, `--capsule-only`, `--ast-only`, `--output <dir>`, `--no-git`.

The script prints a JSON banner as the first line: `{"tier": "T2", "files": 312, ...}`. Read that to know what was produced.

Present the result by linking to `LENS.html` and summarising in one sentence which tier was selected. Do NOT paste the capsule into chat — link to it.

If the user follows up with "use this as my context," append the capsule to their `CLAUDE.md` wrapped in `<!-- lensify-begin -->` / `<!-- lensify-end -->` markers.

## Sub-commands

| Command | What it does | Reference |
|---|---|---|
| `/lensify compact` | Generates WORKING_CONTEXT.md from session state — lets user `/clear` with continuity | `references/conversation-compactor.md` |
| `/lensify stats` | Shows lifetime savings report (run `scripts/stats_cli.py`) | `references/telemetry.md` |
| `/lensify diff <a..b>` | Structural diff between two git refs | `references/complexity-tiers.md` |

## Tier overrides

Auto-selected, but you may override by user intent:

| Signal | Tier |
|---|---|
| "quick summary" / "gist" | T1 |
| "onboard me" / "explain the project" | T2 |
| "monorepo" / "all services" / 1,000+ files | T3 |

## What NOT to do

- Do **not** read the entire codebase into chat. Trust the scan engine's output.
- Do **not** paste the capsule into chat. Link to the file.
- Do **not** invent module names. Preserve confidence tags (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`).
- Do **not** rebuild a lens when `lensify-out/manifest.json` shows current hashes. Link to the existing one.

## References (load on demand)

- `references/complexity-tiers.md` — T1/T2/T3 selection rules + diff mode
- `references/capsule-format.md` — capsule structure + per-tier token budgets
- `references/narrative-prompts.md` — LLM prompt template for the narrative panel
- `references/diagram-selection.md` — Mermaid shape choice (pipeline / layered / hub-spoke / domain-map)
- `references/dedup-hook.md` — Read dedup hook behaviour
- `references/session-capsule.md` — Phase 2 session-activity capsule
- `references/selective-injection.md` — Phase 3 selective capsule injection
- `references/conversation-compactor.md` — Phase 4 `/lensify compact`
- `references/symbol-snippets.md` — Phase 5 SYMBOLS section
- `references/output-compression.md` — Phase 6 tool-output compression
- `references/cross-session-memory.md` — Phase 7 cross-session memory
- `references/telemetry.md` — Phase 8 stats + statusline
- `references/adapter-sdk.md` — Phase 9 framework adapter SDK
