# ProjectLens

> Egyszeri szkennelésű adaptív projekt-lencse + tokenoptimalizált kontextus-kapszula bármely kódbázishoz. Megspórol 70-90% orientációs tokent AI kódolási ügynököknek.

[English](../../README.md) · [Norsk](README.no.md) · **Magyar** · [ภาษาไทย](README.th.md)

## Mi ez

A ProjectLens egy plugin, amely **egyetlen szkenneléssel** (50-150 ms) bármely kódbázist a következőkké alakít:

1. **`LENS.html`** — egyoldalas összefoglaló, amit egy ember 30 másodperc alatt elolvas
2. **`LENS.capsule.md`** — 800-3.600 token kontextusblokk, amit az AI ügynököd felhasznál **30+ nyers fájl elolvasása helyett**
3. **30 framework-adapter** 8 ökoszisztéma-csomagban (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Telepítés

```bash
# Claude Code / Cowork — húzd a projectlens.plugin-t a chatbe
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP szerver
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / szkriptek / CI — CLI
pip install projectlens
# Bármely eszköz, ami kontextus-fájlokat olvas — AGENTS.md mód
projectlens . --install-agents-md
```

## Fő jellemzők

- **Adaptív mélység** (T1/T2/T3)
- **30 framework-adapter** — PyTorch, LangChain, FastAPI, Pinecone, stb.
- **5 munkamenet-hook** (Claude Code)
- **Beszélgetés-tömörítő** — visszanyer 8-25k tokent a munkamenet közepén
- **Tiszta stdlib** — nulla runtime-függőség

## Licenc

MIT.
