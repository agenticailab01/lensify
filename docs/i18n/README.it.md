# ProjectLens

> Lente di progetto adattiva a scansione singola + capsula di contesto ottimizzata per token per qualsiasi codebase. Risparmia il 70-90% dei token di orientamento per agenti di codifica IA.

[English](../../README.md) · [Português](README.pt.md) · **Italiano** · [Polski](README.pl.md)

## Cos'è

ProjectLens è un plugin che con **una singola scansione** (50-150 ms) trasforma qualsiasi codebase in:

1. **`LENS.html`** — un riepilogo di una pagina che un umano legge in 30 secondi
2. **`LENS.capsule.md`** — un blocco di contesto di 800-3.600 token che il tuo agente IA assimila **al posto** di leggere oltre 30 file grezzi
3. **30 adattatori di framework** su 8 pack di ecosistema (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installazione

Quattro canali di distribuzione — scegli quello adatto al tuo strumento:

```bash
# Claude Code / Cowork — trascina projectlens.plugin nella chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — server MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / script / CI — CLI
pip install projectlens
# Qualsiasi strumento che legge file di contesto — modalità AGENTS.md
projectlens . --install-agents-md
```

## Caratteristiche principali

- **Profondità adattiva** — selezione automatica T1 (Schizzo) / T2 (Atlas) / T3 (Bussola)
- **30 adattatori di framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose e altro
- **5 hook di sessione** (Claude Code) — deduplicazione lettura, tracciamento attività, iniezione selettiva, compressione output, memoria tra sessioni
- **Compattatore di conversazione** — `/projectlens compact` per recuperare 8-25k token a metà sessione
- **Stdlib pura** — zero dipendenze a runtime

## Economia dei token

| Fase | Risparmio |
|---|---|
| Orientamento | **70-90%** |
| Riletture | **~25%** (sessioni lunghe) |
| Re-injection per prompt | **~60%** |
| Compattazione a metà sessione | **8-25k** token |

## Test + Prestazioni

527 unit test + 17 budget di performance/sicurezza applicati in CI. Scansione di 500 file: **113 ms**.

## Licenza

MIT.
