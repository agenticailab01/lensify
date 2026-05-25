# ProjectLens

> Lensa proyek adaptif sekali pindai + kapsul konteks yang dioptimalkan untuk token untuk basis kode apa pun. Menghemat 70-90% token orientasi untuk agen pengkodean AI.

[English](../../README.md) · [Tiếng Việt](README.vi.md) · **Bahasa Indonesia** · [Svenska](README.sv.md)

## Apa itu

ProjectLens adalah plugin yang dengan **satu kali pindai** (50-150 ms) mengubah basis kode apa pun menjadi:

1. **`LENS.html`** — ringkasan satu halaman yang dibaca manusia dalam 30 detik
2. **`LENS.capsule.md`** — blok konteks 800-3.600 token yang agen AI Anda serap **alih-alih** membaca 30+ file mentah
3. **30 adaptor framework** di 8 paket ekosistem (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Instalasi

Empat saluran distribusi — pilih yang sesuai dengan alat Anda:

```bash
# Claude Code / Cowork — seret projectlens.plugin ke obrolan
# Cursor / VS Code Copilot / Codex / Gemini CLI — server MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / skrip / CI — CLI
pip install projectlens
# Alat apa pun yang membaca file konteks — mode AGENTS.md
projectlens . --install-agents-md
```

## Fitur utama

- **Kedalaman adaptif** — pemilihan otomatis T1 (Sketsa) / T2 (Atlas) / T3 (Kompas)
- **30 adaptor framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose, dan banyak lagi
- **5 hook sesi** (Claude Code) — dedup baca, pelacakan aktivitas, injeksi selektif, kompresi output, memori lintas-sesi
- **Pemampat percakapan** — `/projectlens compact` untuk memulihkan 8-25k token di tengah sesi
- **Stdlib murni** — nol dependensi runtime

## Ekonomi token

| Tahap | Penghematan |
|---|---|
| Orientasi | **70-90%** |
| Baca ulang | **~25%** (sesi panjang) |
| Re-injeksi per prompt | **~60%** |
| Pemadatan tengah sesi | **8-25k** token |

## Pengujian + Performa

527 unit test + 17 anggaran kinerja/keamanan diberlakukan di CI. Pindai 500 file: **113 ms**.

## Lisensi

MIT.
