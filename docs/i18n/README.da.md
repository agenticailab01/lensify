# ProjectLens

> Adaptiv projektlinse med enkelt-scan + token-optimeret kontekstkapsel for enhver kodebase. Sparer 70-90 % orienteringstokens for AI-kodningsagenter.

[English](../../README.md) · [Suomi](README.fi.md) · **Dansk** · [Norsk](README.no.md)

## Hvad er det

ProjectLens er et plugin, der med **en enkelt scanning** (50-150 ms) omdanner enhver kodebase til:

1. **`LENS.html`** — en sidesammenfatning, som et menneske læser på 30 sekunder
2. **`LENS.capsule.md`** — en kontekstblok på 800-3.600 tokens, som din AI-agent indtager **i stedet for** at læse 30+ rå filer
3. **30 framework-adaptere** på tværs af 8 økosystempakker (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installation

```bash
# Claude Code / Cowork — træk projectlens.plugin ind i chatten
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Ethvert værktøj, der læser kontekstfiler — AGENTS.md-tilstand
projectlens . --install-agents-md
```

## Nøglefunktioner

- **Adaptiv dybde** (T1/T2/T3)
- **30 framework-adaptere** — PyTorch, LangChain, FastAPI, Pinecone, mv.
- **5 sessionshooks** (Claude Code)
- **Samtale-kompaktor** — genvinder 8-25k tokens midt i sessionen
- **Ren stdlib** — nul runtime-afhængigheder

## Licens

MIT.
