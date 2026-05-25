# ProjectLens

> Single-scan adaptieve project-lens + token-geoptimaliseerde context-capsule voor elke codebase. Bespaart 70-90% oriëntatie-tokens voor AI-coding-agents.

[English](../../README.md) · [Polski](README.pl.md) · **Nederlands** · [Türkçe](README.tr.md)

## Wat is het

ProjectLens is een plugin die met **één scan** (50-150 ms) elke codebase verandert in:

1. **`LENS.html`** — een eenpaginasamenvatting die een mens in 30 seconden leest
2. **`LENS.capsule.md`** — een contextblok van 800-3.600 tokens dat je AI-agent opneemt **in plaats van** 30+ ruwe bestanden te lezen
3. **30 framework-adapters** over 8 ecosysteempakketten (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installatie

Vier distributiekanalen — kies wat bij je tool past:

```bash
# Claude Code / Cowork — sleep projectlens.plugin naar de chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Elke tool die contextbestanden leest — AGENTS.md-modus
projectlens . --install-agents-md
```

## Belangrijkste functies

- **Adaptieve diepte** — automatische selectie T1 (Schets) / T2 (Atlas) / T3 (Kompas)
- **30 framework-adapters** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose en meer
- **5 sessie-hooks** (Claude Code) — read dedup, activity tracking, selectieve injectie, output-compressie, cross-session memory
- **Gesprek-compactor** — `/projectlens compact` om 8-25k tokens halverwege de sessie terug te winnen
- **Pure stdlib** — nul runtime-afhankelijkheden

## Token-economie

| Fase | Besparing |
|---|---|
| Oriëntatie | **70-90%** |
| Herlezen | **~25%** (lange sessies) |
| Per-prompt re-injection | **~60%** |
| Halverwege sessie-compactie | **8-25k** tokens |

## Tests + Prestaties

527 unit-tests + 17 perf-/security-budgetten afgedwongen in CI. Scan van 500 bestanden: **113 ms**.

## Licentie

MIT.
