# ProjectLens

> Lentille de projet adaptative à scan unique + capsule de contexte optimisée en jetons pour toute base de code. Économise 70-90 % de jetons d'orientation pour les agents de codage IA.

[English](../../README.md) · [Deutsch](README.de.md) · **Français** · [Español](README.es.md)

## Qu'est-ce que c'est

ProjectLens est un plugin qui transforme n'importe quelle base de code en **un seul scan** (50-150 ms) en :

1. **`LENS.html`** — un résumé d'une page qu'un humain lit en 30 secondes
2. **`LENS.capsule.md`** — un bloc de contexte de 800-3 600 jetons que votre agent IA ingère **à la place** de la lecture de 30+ fichiers
3. **30 adaptateurs de framework** sur 8 packs d'écosystème (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Installation

Quatre canaux de distribution — choisissez celui qui correspond à votre outil :

```bash
# Claude Code / Cowork — glisser-déposer projectlens.plugin dans le chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — serveur MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Tout outil qui lit les fichiers de contexte — mode AGENTS.md
projectlens . --install-agents-md
```

## Fonctionnalités clés

- **Profondeur adaptative** — sélection automatique T1 (Esquisse) / T2 (Atlas) / T3 (Boussole)
- **30 adaptateurs de framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose et plus
- **5 hooks de session** (Claude Code) — déduplication de lecture, suivi d'activité, injection sélective, compression de sortie, mémoire inter-sessions
- **Compacteur de conversation** — `/projectlens compact` pour récupérer 8-25k jetons en milieu de session
- **Stdlib pure** — zéro dépendance runtime

## Économie de jetons

| Étape | Économies |
|---|---|
| Orientation | **70-90 %** |
| Re-lectures | **~25 %** (longues sessions) |
| Re-injection par prompt | **~60 %** |
| Compaction en milieu de session | **8-25k** jetons |

## Tests + Performance

527 tests unitaires + 17 budgets de perf/sécurité appliqués en CI. Scan de 500 fichiers : **113 ms**.

## Licence

MIT.
