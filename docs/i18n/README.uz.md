# ProjectLens

> Har qanday kodlar bazasi uchun bir martalik skanerli moslashuvchan loyiha linzasi + tokenga optimallashtirilgan kontekst kapsulasi. AI kodlash agentlari uchun 70-90% yo'naltirish tokenlarini tejaydi.

[English](../../README.md) · [ภาษาไทย](README.th.md) · **O'zbekcha** · [简体中文](README.zh-CN.md)

## Bu nima

ProjectLens — bu **bir martalik skanerlash** bilan (50-150 ms) har qanday kodlar bazasini quyidagilarga aylantiradigan plagin:

1. **`LENS.html`** — odam 30 soniyada o'qiy oladigan bir sahifali xulosa
2. **`LENS.capsule.md`** — 800-3 600 tokenli kontekst bloki, AI agentingiz uni 30+ xom fayl o'qish **o'rniga** o'zlashtiradi
3. **30 freymvork adapteri** 8 ekotizim paketida (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## O'rnatish

```bash
# Claude Code / Cowork — projectlens.plugin'ni chatga sudrang
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP server
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skriptlar / CI — CLI
pip install projectlens
# Kontekst fayllarini o'qiydigan har qanday vosita — AGENTS.md rejimi
projectlens . --install-agents-md
```

## Asosiy xususiyatlar

- **Moslashuvchan chuqurlik** (T1/T2/T3)
- **30 freymvork adapteri** — PyTorch, LangChain, FastAPI, Pinecone va boshqalar
- **5 sessiya ilgagi** (Claude Code)
- **Suhbat kompaktori** — sessiya o'rtasida 8-25k tokenni qaytaradi
- **Sof stdlib** — runtime bog'liqliklari nol

## Litsenziya

MIT.
