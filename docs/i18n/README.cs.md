# ProjectLens

> Adaptivní projektový objektiv s jediným skenováním + kontextová kapsle optimalizovaná pro tokeny pro libovolnou kódovou základnu. Šetří 70-90 % orientačních tokenů pro AI kódovací agenty.

[English](../../README.md) · [Română](README.ro.md) · **Čeština** · [Suomi](README.fi.md)

## Co to je

ProjectLens je plugin, který **jedním skenováním** (50-150 ms) přemění libovolnou kódovou základnu na:

1. **`LENS.html`** — jednostránkové shrnutí, které člověk přečte za 30 sekund
2. **`LENS.capsule.md`** — blok kontextu o 800-3 600 tokenech, který váš AI agent přijímá **místo** čtení 30+ souborů
3. **30 framework adaptérů** v 8 ekosystémových balíčcích (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalace

```bash
# Claude Code / Cowork — přetáhněte projectlens.plugin do chatu
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skripty / CI — CLI
pip install projectlens
# Jakýkoli nástroj čtoucí kontextové soubory — režim AGENTS.md
projectlens . --install-agents-md
```

## Klíčové funkce

- **Adaptivní hloubka** (T1/T2/T3)
- **30 framework adaptérů** — PyTorch, LangChain, FastAPI, Pinecone, atd.
- **5 háčků relace** (Claude Code)
- **Kompaktor konverzace** — získá zpět 8-25k tokenů uprostřed relace
- **Čistá stdlib** — nulové runtime závislosti

## Licence

MIT.
