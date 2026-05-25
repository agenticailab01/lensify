# ProjectLens

> Yhden skannauksen mukautuva projektilinssi + token-optimoitu kontekstikapseli mille tahansa koodikannalle. Säästää 70-90 % orientointitokeneista AI-koodausagenteille.

[English](../../README.md) · [Čeština](README.cs.md) · **Suomi** · [Dansk](README.da.md)

## Mikä se on

ProjectLens on lisäosa, joka **yhdellä skannauksella** (50-150 ms) muuntaa minkä tahansa koodikannan:

1. **`LENS.html`** — yhden sivun yhteenveto, jonka ihminen lukee 30 sekunnissa
2. **`LENS.capsule.md`** — 800-3 600 tokenin kontekstilohko, jonka AI-agenttisi imee **30+ raakatiedoston lukemisen sijaan**
3. **30 framework-sovitinta** 8 ekosysteemipaketissa (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Asennus

```bash
# Claude Code / Cowork — vedä projectlens.plugin chattiin
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-palvelin
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skriptit / CI — CLI
pip install projectlens
# Mikä tahansa työkalu, joka lukee kontekstitiedostoja — AGENTS.md-tila
projectlens . --install-agents-md
```

## Pääominaisuudet

- **Mukautuva syvyys** (T1/T2/T3)
- **30 framework-sovitinta** — PyTorch, LangChain, FastAPI, Pinecone, jne.
- **5 istunnon koukkua** (Claude Code)
- **Keskustelukompaktori** — palauttaa 8-25k tokenia kesken istunnon
- **Puhdas stdlib** — nolla ajonaikaista riippuvuutta

## Lisenssi

MIT.
