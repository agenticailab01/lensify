# ProjectLens

> Lente de proyecto adaptativa de escaneo único + cápsula de contexto optimizada por tokens para cualquier base de código. Ahorra 70-90 % de tokens de orientación para agentes de codificación IA.

[English](../../README.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · **Español**

## Qué es

ProjectLens es un plugin que convierte cualquier base de código en **un solo escaneo** (50-150 ms) en:

1. **`LENS.html`** — un resumen de una página que un humano lee en 30 segundos
2. **`LENS.capsule.md`** — un bloque de contexto de 800-3.600 tokens que tu agente IA ingiere **en lugar** de leer 30+ archivos
3. **30 adaptadores de framework** en 8 paquetes de ecosistema (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalación

Cuatro canales de distribución — elige el que coincida con tu herramienta:

```bash
# Claude Code / Cowork — arrastra y suelta projectlens.plugin en el chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — servidor MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Cualquier herramienta que lea archivos de contexto — modo AGENTS.md
projectlens . --install-agents-md
```

## Características principales

- **Profundidad adaptativa** — selección automática T1 (Boceto) / T2 (Atlas) / T3 (Brújula)
- **30 adaptadores de framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose y más
- **5 hooks de sesión** (Claude Code) — deduplicación de lectura, seguimiento de actividad, inyección selectiva, compresión de salida, memoria entre sesiones
- **Compactador de conversación** — `/projectlens compact` para recuperar 8-25k tokens a mitad de sesión
- **Stdlib pura** — cero dependencias en tiempo de ejecución

## Economía de tokens

| Etapa | Ahorro |
|---|---|
| Orientación | **70-90 %** |
| Relecturas | **~25 %** (sesiones largas) |
| Re-inyección por prompt | **~60 %** |
| Compactación a mitad de sesión | **8-25k** tokens |

## Tests + Rendimiento

527 tests unitarios + 17 presupuestos de rendimiento/seguridad aplicados en CI. Escaneo de 500 archivos: **113 ms**.

## Licencia

MIT.
