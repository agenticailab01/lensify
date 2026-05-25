# ProjectLens

> Herhangi bir kod tabanı için tek taramalı uyarlanabilir proje merceği + token-optimize edilmiş bağlam kapsülü. AI kodlama ajanları için %70-90 yönelim tokeni tasarrufu sağlar.

[English](../../README.md) · [Nederlands](README.nl.md) · **Türkçe** · [Українська](README.uk.md)

## Nedir

ProjectLens, **tek bir taramayla** (50-150 ms) herhangi bir kod tabanını şuna dönüştüren bir eklentidir:

1. **`LENS.html`** — bir insanın 30 saniyede okuyabileceği tek sayfalık özet
2. **`LENS.capsule.md`** — 30+ ham dosya okumak **yerine** AI ajanınızın aldığı 800-3.600 tokenlık bağlam bloğu
3. **30 framework adaptörü** 8 ekosistem paketi üzerinde (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Kurulum

Dört dağıtım kanalı — aracınıza uygun olanı seçin:

```bash
# Claude Code / Cowork — projectlens.plugin'i sohbete sürükleyip bırakın
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP sunucusu
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / komut dosyaları / CI — CLI
pip install projectlens
# Bağlam dosyalarını okuyan herhangi bir araç — AGENTS.md modu
projectlens . --install-agents-md
```

## Temel özellikler

- **Uyarlanabilir derinlik** — otomatik seçim T1 (Taslak) / T2 (Atlas) / T3 (Pusula)
- **30 framework adaptörü** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose ve daha fazlası
- **5 oturum kancası** (Claude Code) — okuma tekilleştirme, etkinlik izleme, seçici enjeksiyon, çıktı sıkıştırma, oturumlar arası bellek
- **Konuşma sıkıştırıcı** — `/projectlens compact` ile oturum ortasında 8-25k token geri kazanın
- **Saf stdlib** — sıfır çalışma zamanı bağımlılığı

## Token ekonomisi

| Aşama | Tasarruf |
|---|---|
| Yönelim | **%70-90** |
| Tekrar okuma | **~%25** (uzun oturumlar) |
| Komut başına yeniden enjeksiyon | **~%60** |
| Oturum ortası sıkıştırma | **8-25k** token |

## Testler + Performans

CI'da 527 birim testi + 17 performans/güvenlik bütçesi zorlandı. 500 dosya taraması: **113 ms**.

## Lisans

MIT.
