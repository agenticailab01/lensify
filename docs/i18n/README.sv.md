# ProjectLens

> Single-scan adaptiv projektlins + token-optimerad kontextkapsel för vilken kodbas som helst. Sparar 70-90 % orienteringstoken för AI-kodningsagenter.

[English](../../README.md) · [Bahasa Indonesia](README.id.md) · **Svenska** · [Ελληνικά](README.el.md)

## Vad är det

ProjectLens är ett plugin som med **en enda skanning** (50-150 ms) förvandlar vilken kodbas som helst till:

1. **`LENS.html`** — en sidsammanfattning som en människa läser på 30 sekunder
2. **`LENS.capsule.md`** — ett kontextblock på 800-3 600 token som din AI-agent intar **istället för** att läsa 30+ råa filer
3. **30 framework-adaptrar** över 8 ekosystempack (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installation

Fyra distributionskanaler — välj den som passar ditt verktyg:

```bash
# Claude Code / Cowork — dra projectlens.plugin till chatten
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skript / CI — CLI
pip install projectlens
# Vilket verktyg som helst som läser kontextfiler — AGENTS.md-läge
projectlens . --install-agents-md
```

## Huvudfunktioner

- **Adaptivt djup** — automatiskt val T1 (Skiss) / T2 (Atlas) / T3 (Kompass)
- **30 framework-adaptrar** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose och mer
- **5 sessionshooks** (Claude Code) — läs-dedup, aktivitetsspårning, selektiv injektion, output-komprimering, sessionsöverskridande minne
- **Konversationskompaktor** — `/projectlens compact` för att återvinna 8-25k token mitt i sessionen
- **Ren stdlib** — noll runtime-beroenden

## Token-ekonomi

| Steg | Besparing |
|---|---|
| Orientering | **70-90 %** |
| Omläsningar | **~25 %** (långa sessioner) |
| Per-prompt re-injektion | **~60 %** |
| Mittsession-kompaktion | **8-25k** token |

## Tester + Prestanda

527 enhetstester + 17 prestanda-/säkerhetsbudgetar tvingade i CI. Skanning av 500 filer: **113 ms**.

## Licens

MIT.
