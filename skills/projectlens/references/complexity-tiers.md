# Complexity Tier Rules

ProjectLens chooses one of three tiers based on measured signals. The exact algorithm is in `scripts/complexity.py` — this file documents the *intent*.

## T1 — Sketch

**When:** small, focused project a single person can hold in their head.

Trigger when ALL of:
- File count (non-vendored) < 50
- Total LOC < 5,000
- Primary-language share ≥ 80%
- No nested service directories (no `services/*/src/`, `apps/*/src/`)

**Lens shows:**
- One-sentence "What this is"
- 5-box diagram (auto-shape: pipeline, hub-spoke, or layered)
- 3-line narrative
- Top 3 hotspots
- Up to 5 inferred risks

**Capsule target:** ≤ 500 tokens.

## T2 — Atlas

**When:** medium project, multi-module, but still one cohesive app.

Trigger when ANY of:
- File count between 50 and 1,000
- LOC between 5,000 and 100,000
- 2–4 top-level module directories
- Multi-language but dominant language ≥ 60%

**Lens shows:**
- Project summary paragraph (3–4 sentences)
- Layered diagram (presentation / domain / data / infra) OR module hub-spoke
- 180-word Day-1 narrative
- Module table (name, purpose, hotspot rank, lines)
- Top 5 hotspots with churn metrics
- Confidence-tagged risks

**Capsule target:** ≤ 1,500 tokens.

## T3 — Compass

**When:** monorepo, large multi-service app, or a polyglot codebase.

Trigger when ANY of:
- File count > 1,000
- LOC > 100,000
- 5+ top-level module/service directories
- Detected monorepo markers: `lerna.json`, `pnpm-workspace.yaml`, `nx.json`, `turbo.json`, top-level `services/`, `apps/`, `packages/`

**Lens shows:**
- Executive summary (5 sentences)
- Domain map (each domain is a clickable region in the HTML; expands inline)
- Per-domain hotspots
- Cross-domain dependency callouts
- Confidence-tagged inter-service risks
- Linked sub-capsules: one per domain, written to `projectlens-out/capsules/<domain>.md`

**Capsule target:** main ≤ 2,500 tokens, plus sub-capsules ≤ 800 tokens each.

## Edge cases

| Project shape | Resolution |
|---|---|
| Empty directory | Refuse with friendly message |
| Only docs (no code) | Run in `docs-only` mode (T1 always, narrative-heavy) |
| Generated/vendored code dominates | Re-measure excluding `node_modules`, `vendor`, `dist`, `.venv`, `target`, `.next`, `coverage` |
| Two roughly equal languages | T2 minimum; show language-split badge in lens |
| Git repository absent | Skip hotspots panel; emit warning; tier still applies |

## How to override

Users override via `--tier T1|T2|T3`. The skill's invoking model can also override when the user's intent is clearly "give me the gist" (T1) or "show me everything" (T3).

The script logs the chosen tier and the reason to `lens.json` under `tier_decision.reason`. Always preserve that field — it's the receipt for the choice.
