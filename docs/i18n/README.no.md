# ProjectLens

> Adaptiv prosjektlinse med enkelt-skann + token-optimalisert kontekstkapsel for enhver kodebase. Sparer 70-90 % orienteringstokens for AI-kodingsagenter.

[English](../../README.md) · [Dansk](README.da.md) · **Norsk** · [Magyar](README.hu.md)

## Hva er det

ProjectLens er et plugin som med **én enkelt skanning** (50-150 ms) omgjør enhver kodebase til:

1. **`LENS.html`** — et énsidet sammendrag som et menneske leser på 30 sekunder
2. **`LENS.capsule.md`** — en kontekstblokk på 800-3.600 tokens som din AI-agent inntar **i stedet for** å lese 30+ rå filer
3. **30 framework-adaptere** på tvers av 8 økosystempakker (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installasjon

```bash
# Claude Code / Cowork — dra projectlens.plugin inn i chatten
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skript / CI — CLI
pip install projectlens
# Ethvert verktøy som leser kontekstfiler — AGENTS.md-modus
projectlens . --install-agents-md
```

## Nøkkelfunksjoner

- **Adaptiv dybde** (T1/T2/T3)
- **30 framework-adaptere** — PyTorch, LangChain, FastAPI, Pinecone, m.m.
- **5 sesjonshooks** (Claude Code)
- **Samtale-kompaktor** — gjenvinner 8-25k tokens midt i sesjonen
- **Ren stdlib** — null runtime-avhengigheter

## Lisens

MIT.
