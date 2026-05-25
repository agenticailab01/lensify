# ProjectLens

> Lentilă adaptivă de proiect cu scanare unică + capsulă de context optimizată pentru token-uri pentru orice bază de cod. Economisește 70-90% din token-urile de orientare pentru agenții de codificare AI.

[English](../../README.md) · [Ελληνικά](README.el.md) · **Română** · [Čeština](README.cs.md)

## Ce este

ProjectLens este un plugin care printr-o **singură scanare** (50-150 ms) transformă orice bază de cod în:

1. **`LENS.html`** — un rezumat de o pagină pe care un om îl citește în 30 de secunde
2. **`LENS.capsule.md`** — un bloc de context de 800-3.600 token-uri pe care agentul tău AI îl asimilează **în loc** să citească 30+ fișiere brute
3. **30 adaptoare de framework** în 8 pachete de ecosistem (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalare

```bash
# Claude Code / Cowork — trage și plasează projectlens.plugin în chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — server MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripturi / CI — CLI
pip install projectlens
# Orice instrument care citește fișiere de context — mod AGENTS.md
projectlens . --install-agents-md
```

## Caracteristici principale

- **Adâncime adaptivă** (T1/T2/T3)
- **30 adaptoare de framework** — PyTorch, LangChain, FastAPI, Pinecone, etc.
- **5 hook-uri de sesiune** (Claude Code)
- **Compactor de conversație** — recuperează 8-25k token-uri la mijlocul sesiunii
- **Stdlib pură** — zero dependențe runtime

## Licență

MIT.
