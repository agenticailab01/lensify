# ProjectLens

> Einzel-Scan adaptive Projekt-Linse + Token-optimierte Kontext-Kapsel für jede Codebasis. Spart 70-90 % Orientierungstokens für KI-Coding-Agenten.

[English](../../README.md) · **Deutsch** · [Français](README.fr.md) · [Español](README.es.md)

## Was ist es

ProjectLens ist ein Plugin, das mit **einem einzigen Scan** (50-150 ms) jede Codebasis verwandelt in:

1. **`LENS.html`** — eine einseitige Zusammenfassung, die ein Mensch in 30 Sekunden liest
2. **`LENS.capsule.md`** — ein 800-3.600-Token-Kontextblock, den dein KI-Agent **anstelle** des Lesens von 30+ Dateien verarbeitet
3. **30 Framework-Adapter** über 8 Ökosystem-Packs (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installation

Vier Verteilungskanäle — wähle den, der zu deinem Tool passt:

```bash
# Claude Code / Cowork — projectlens.plugin in den Chat ziehen
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP-Server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / Skripte / CI — CLI
pip install projectlens
# Jedes Tool, das Kontextdateien liest — AGENTS.md-Modus
projectlens . --install-agents-md
```

## Hauptfunktionen

- **Adaptive Tiefe** — automatische Auswahl T1 (Skizze) / T2 (Atlas) / T3 (Kompass)
- **30 Framework-Adapter** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose und mehr
- **5 Session-Hooks** (Claude Code) — Read-Dedup, Aktivitätsverfolgung, selektive Injektion, Output-Komprimierung, sitzungsübergreifender Speicher
- **Konversations-Kompaktor** — `/projectlens compact` zur Wiedererlangung von 8-25k Tokens in der Mitte einer Session
- **Reine Stdlib** — null Runtime-Abhängigkeiten

## Token-Ökonomie

| Stufe | Einsparungen |
|---|---|
| Orientierung | **70-90 %** |
| Wiederholungs-Lesen | **~25 %** (lange Sessions) |
| Pro-Prompt-Re-Injection | **~60 %** |
| Mitten-Session-Kompaktion | **8-25k** Tokens |

## Tests + Performance

527 Unit-Tests + 17 Performance-/Sicherheits-Budgets in CI durchgesetzt. Scan von 500 Dateien: **113 ms**.

## Lizenz

MIT.
