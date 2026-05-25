# ProjectLens

> Adaptacyjna soczewka projektu jednorazowego skanowania + kapsuła kontekstu zoptymalizowana pod kątem tokenów dla dowolnej bazy kodu. Oszczędza 70-90% tokenów orientacyjnych dla agentów kodowania AI.

[English](../../README.md) · [Italiano](README.it.md) · **Polski** · [Nederlands](README.nl.md)

## Co to jest

ProjectLens to wtyczka, która **jednym skanowaniem** (50-150 ms) zmienia dowolną bazę kodu w:

1. **`LENS.html`** — jednostronicowe podsumowanie, które człowiek czyta w 30 sekund
2. **`LENS.capsule.md`** — blok kontekstu o objętości 800-3 600 tokenów, który Twój agent AI przyswaja **zamiast** czytania 30+ surowych plików
3. **30 adapterów frameworków** w 8 paczkach ekosystemu (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalacja

Cztery kanały dystrybucji — wybierz pasujący do swojego narzędzia:

```bash
# Claude Code / Cowork — przeciągnij projectlens.plugin do czatu
# Cursor / VS Code Copilot / Codex / Gemini CLI — serwer MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skrypty / CI — CLI
pip install projectlens
# Każde narzędzie czytające pliki kontekstu — tryb AGENTS.md
projectlens . --install-agents-md
```

## Kluczowe funkcje

- **Adaptacyjna głębokość** — automatyczny wybór T1 (Szkic) / T2 (Atlas) / T3 (Kompas)
- **30 adapterów frameworków** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose i więcej
- **5 hooków sesji** (Claude Code) — deduplikacja odczytu, śledzenie aktywności, selektywne wstrzykiwanie, kompresja wyjścia, pamięć międzysesyjna
- **Kompaktor konwersacji** — `/projectlens compact` aby odzyskać 8-25k tokenów w środku sesji
- **Czysty stdlib** — zero zależności w runtime

## Ekonomia tokenów

| Etap | Oszczędności |
|---|---|
| Orientacja | **70-90%** |
| Powtórne odczyty | **~25%** (długie sesje) |
| Ponowne wstrzyknięcie na prompt | **~60%** |
| Kompakcja w połowie sesji | **8-25k** tokenów |

## Testy + Wydajność

527 testów jednostkowych + 17 budżetów wydajności/bezpieczeństwa wymuszonych w CI. Skanowanie 500 plików: **113 ms**.

## Licencja

MIT.
