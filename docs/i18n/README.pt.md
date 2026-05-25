# ProjectLens

> Lente de projeto adaptativa de varredura única + cápsula de contexto otimizada por tokens para qualquer base de código. Economiza 70-90% de tokens de orientação para agentes de codificação IA.

[English](../../README.md) · [Español](README.es.md) · **Português** · [Italiano](README.it.md)

## O que é

ProjectLens é um plugin que transforma qualquer base de código com **uma única varredura** (50-150 ms) em:

1. **`LENS.html`** — um resumo de uma página que um humano lê em 30 segundos
2. **`LENS.capsule.md`** — um bloco de contexto de 800-3.600 tokens que seu agente IA ingere **em vez** de ler mais de 30 arquivos
3. **30 adaptadores de framework** em 8 packs de ecossistema (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalação

Quatro canais de distribuição — escolha o que combina com sua ferramenta:

```bash
# Claude Code / Cowork — arraste projectlens.plugin para o chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — servidor MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Qualquer ferramenta que leia arquivos de contexto — modo AGENTS.md
projectlens . --install-agents-md
```

## Principais recursos

- **Profundidade adaptativa** — selecione automaticamente T1 (Esboço) / T2 (Atlas) / T3 (Bússola)
- **30 adaptadores de framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose e mais
- **5 hooks de sessão** (Claude Code) — desduplicação de leitura, rastreamento de atividade, injeção seletiva, compressão de saída, memória entre sessões
- **Compactador de conversação** — `/projectlens compact` para recuperar 8-25k tokens no meio da sessão
- **Stdlib pura** — zero dependências de runtime

## Economia de tokens

| Estágio | Economia |
|---|---|
| Orientação | **70-90%** |
| Releituras | **~25%** (sessões longas) |
| Re-injeção por prompt | **~60%** |
| Compactação no meio da sessão | **8-25k** tokens |

## Testes + Performance

527 testes unitários + 17 orçamentos de performance/segurança aplicados em CI. Varredura de 500 arquivos: **113 ms**.

## Licença

MIT.
