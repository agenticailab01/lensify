# Lensify v0.15.0 — competitive benchmark

This is a sober, structured assessment of where Lensify stands against the AI-coding context tools shipping today.

## Tool categories

We split competitors into two groups because they solve different problems:

1. **Direct competitors (same category).** Graphify, Caveman, Repomix, Aider's repo-map, Claude-Mem — all do *structural orientation* of a codebase. Lensify fits here and **leads decisively**.
2. **Adjacent tools (different category).** Cursor's `@codebase`, Sourcegraph Cody, Continue.dev — these do *semantic vector search*. Different problem class; Lensify doesn't try to do this.

We separate **structural extraction** (what Lensify does) from **semantic search** (what Cody does) because they're different problem classes and shouldn't be compared head-to-head.

## Measured performance (synthetic, current session)

| Project size | Files | Scan time | Capsule size | Adapter sections rendered |
|---:|---:|---:|---:|---:|
| Tiny | 20 | **41 ms** | 402 tok | 5 |
| Medium | 100 | **29 ms** | 529 tok | 5 |
| Large | 500 | **113 ms** | 529 tok | 5 |

Capsule size stays **bounded by tier budget** regardless of project size — this is the core architectural promise.

**Hook overhead** (per Claude Code event):
- `dedup_hook` startup: < 250 ms cold, ~20-30 ms warm
- Hook output envelope: ≤ 500 tokens per event (CI-enforced)
- Activity tracking + injection: amortised over session, near-zero per event

**Test status:** 544 tests (incl. 17 perf/security CI budgets) pass.

---

## Competitive matrix

We compare against eight tools that operate in adjacent spaces. Rating per cell: **✓** = clear support, **~** = partial, **✗** = not provided. We rate Lensify last to keep the table honest.

| Capability | Repomix | Aider repo-map | Cursor @codebase | Sourcegraph Cody | Continue.dev | Graphify | Caveman | Claude-Mem | **Lensify** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Single-pass codebase summary | ✓ | ✓ | ✓ (search-based) | ✓ (search-based) | ✓ | ~ | ✓ | ✗ | **✓** |
| Token-bounded output | ~ | ~ | ✗ | ✗ | ~ | ✗ | ~ | ✓ | **✓ (locked by tier)** |
| Adaptive depth (auto-tier) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ T1/T2/T3** |
| Framework-aware extraction | ✗ | ✗ | ~ (heuristic) | ~ | ~ | ✗ | ~ | ✗ | **✓ 30 adapters / 8 packs** |
| Confidence tags on output | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ EXTRACTED/INFERRED/AMBIGUOUS** |
| Read dedup (in-session) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | **✓ hook** |
| Selective context injection | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ UserPromptSubmit hook** |
| Tool-output compression | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓ 9 deterministic compressors** |
| Mid-session compaction | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | **✓ /lensify compact** |
| Cross-session memory | ✗ | ✗ | ~ (Cursor only) | ✓ | ✗ | ✗ | ✗ | ✓ | **✓ per-project, opt-out** |
| One-page HTML visual | ✗ | ✗ | ✗ | ✓ (web UI) | ✗ | ✓ | ✗ | ✗ | **✓ LENS.html** |
| Multi-tool compatibility | CLI | Aider-only | Cursor-only | Sourcegraph-only | VS Code-only | CLI | CLI | Claude Code-only | **✓ 4 channels (plugin/MCP/CLI/AGENTS.md)** |
| Native MCP server | ✗ | ✗ | host | host | host | ✗ | ✗ | ✗ | **✓ stdlib stdio** |
| Custom adapter SDK | ✗ | ✗ | ✗ | ~ (LSP-style) | ~ | ✗ | ✗ | ✗ | **✓ ~100 LOC template** |
| User-defined adapters | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | **✓ opt-in `.lensify/frameworks/`** |
| Semantic / vector search | ✗ | ~ | ✓ | ✓ | ✓ | ✗ | ✗ | ~ | **✗** |
| Embedding store integration | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | **✗ (adapter surfaces them, doesn't run them)** |
| Plugin size | ~80 KB | bundled | bundled | hosted | bundled | n/a | ~10 KB | ~50 KB | **203 KB** |
| Dependencies | none | aider | Cursor | account | VS Code | none | minimal | mcp SDK | **stdlib only** |
| Security audit (CI-enforced) | ✗ | ✗ | hosted | hosted | ✗ | ✗ | ✗ | ✗ | **✓ 3 static-analysis tests** |
| Open source | ✓ | ✓ | ✗ | ~ (Cody) | ✓ | ✓ | ✓ | ✓ | **✓ MIT** |

---

## Where Lensify **leads**

**1. Adaptive depth (T1/T2/T3) — only tool that auto-scales.**
Every other tool produces a fixed-shape output. Lensify reads project size + structure and picks the right depth. A 12-file script gets a sketch; a 4,000-file monorepo gets a compass. One page either way.

**2. Framework-aware structural extraction — 30 adapters across 8 packs.**
Repomix and Caveman dump file text. Aider's repo-map gives function signatures. Lensify emits **structural records** per framework: `engine LLM ← Llama-3-8b-Instruct`, `service api → ports 8000`, `model User → table users · 4 cols`, `graph workflow → nodes: classify, search, respond`. Confidence-tagged so the agent calibrates trust.

**3. Hook integration in Claude Code — five hooks that compound.**
No other tool ships dedup + activity tracking + selective injection + output compression + cross-session memory as an integrated unit. Savings are reported honestly as **realized vs potential**: orientation (~70-90%) and compaction (8-25k) are realized; repeat-read (~25%) is realized only under `LENSIFY_DEDUP_ENFORCE=1` (advisory otherwise); output compression is realized via the `lensify run` wrapper and potential via the passive hook; selective injection (~60%) is potential vs. a full-capsule baseline. `/lensify stats` headlines the realized figure so the numbers never overstate.

**4. Multi-channel distribution.**
Plugin (Claude Code/Cowork) + MCP (Cursor/Codex/VS Code/Gemini/Antigravity/Kiro/Trae/OpenCode) + CLI (Aider/Copilot CLI/CI) + AGENTS.md (anything else). Same engine, four artifacts. Nobody else covers this breadth from one project.

**5. Security + governance posture is the highest in the category.**
- `SECURITY.md` with threat model
- `GOVERNANCE.md` with scope-of-use and abuse mitigations
- CI-enforced bans on `exec` / `eval` / `pickle` / `shell=True` / `os.system`
- Outbound HTTP confined to a single allowlisted endpoint
- User-adapter loader opt-in via long env var
- Every persistent surface has documented opt-out
- 1 MB file read cap

Repomix, Aider, and Continue have none of these guard rails. Cody and Cursor are hosted services with different threat models — not directly comparable.

**6. Pure stdlib — zero pip-install runtime dependency.**
The plugin runs anywhere Python 3.9+ runs. No virtualenv, no transitive web of deps. Repomix needs Node. Continue needs VS Code. Cody needs an account.

**7. CI-enforced performance budgets.**
14 perf budgets + 3 security tests fail the build if regressed. No other tool in this list ships this discipline. Adding 25 framework adapters would be impossible without it — they'd silently slow the scan.

---

## Where Lensify **ties or matches**

- **Single-pass codebase summary** — Repomix, Aider, Caveman, Continue.dev all do this. Lensify does it better-structured, but the core capability is shared.
- **Cross-session memory** — Cody and Claude-Mem both do this. Lensify matches at functional parity; the differentiator is the opt-out env var.
- **Open-source** — most direct competitors are MIT/Apache. Standard.

---

## Where Lensify **does not compete**

**1. Semantic / vector search.**
Cursor's `@codebase`, Sourcegraph Cody, and Continue.dev all build embedding indexes for semantic retrieval. Lensify does **structural** extraction — no embeddings, no vector DB, no semantic query. Different category.

This is a deliberate scope choice: structural extraction is **deterministic, fast, and cheap**. Semantic search requires an embedding model + vector store + index maintenance — much more infrastructure, much higher operational cost, and only marginal benefit for the "I want to understand this codebase" use case.

Lensify *surfaces* vector DBs (Pinecone, Weaviate, Qdrant, Chroma adapters) but doesn't *run* one. That's the right level for our scope.

**2. Hosted code-search at enterprise scale.**
Sourcegraph Cody indexes hundreds of millions of LOC across thousands of repos. Lensify runs per-project on a developer laptop. Different problems.

**3. VS Code-native UX.**
Continue.dev and Cline have rich VS Code UIs. Lensify via MCP works in VS Code but the UX is a chat-side tool call, not a custom panel.

---

## Honest gaps + future work

| Gap | Severity | Plan |
|---|---|---|
| No semantic search | Out of scope — deliberate. | Won't add; orthogonal capability. |
| Plugin works only in Claude Code/Cowork; hooks don't port | Acknowledged. | MCP/CLI/AGENTS.md channels (v0.15.0) cover the rest at 70-90% of value. |
| No JavaScript/TypeScript adapter ecosystem (only Vue SFC) | Real gap. | Next sprint candidates: Next.js, Astro, SvelteKit, NestJS, tRPC. |
| No Rust / Go / Java framework adapters | Real gap. | Lower priority — AI dev is mostly Python. Future. |
| No GUI for the adapter SDK | Minor. | CLI scaffolder (`lensify new-adapter X`) is ~50 LOC; could ship. |
| Adapter quality varies (some regexes are heuristic) | Acknowledged via INFERRED tags. | Per-adapter improvements over time as users report misfires. |

---

## Verdict

**Lensify fits the competition and leads it on most dimensions that matter for the "I want my agent to understand this codebase fast and cheap" use case.**

- **Leads** on adaptive depth, framework awareness, hook integration, multi-channel distribution, security, and performance discipline.
- **Ties or matches** on single-pass summarisation, cross-session memory, and open-source status.
- **Doesn't compete** on semantic search and enterprise-scale hosting — by deliberate scope choice.

The category-defining differentiator is the **framework adapter SDK with 30 shipped adapters**. No other tool in the list goes from "300 files of Python" to "here's your LLM, your DB models, your routes, your training loop, your vector store, your experiment tracker, your UI components" in 100 ms. That's the moat.

The category-typical thing we **don't** do is semantic search — and we're correct not to. Adding it would mean a 10× larger plugin, mandatory embedding models, vector DB ops cost, and value-add only at scales where Cody already dominates.

If you're an AI engineer working on a Python AI/ML codebase, Lensify v0.15.0 is the most capable, lightest, fastest tool shipping for first-pass orientation today.
