# ProjectLens

> 任意のコードベース向けの単一スキャン適応型プロジェクトレンズ + トークン最適化コンテキストカプセル。AI コーディングエージェント向けにオリエンテーショントークンを 70-90% 削減。

[English](../../README.md) · [简体中文](README.zh-CN.md) · **日本語** · [한국어](README.ko.md)

## 何ですか

ProjectLens は、**1 回のスキャン** (50-150 ms) で任意のコードベースを次のものに変換するプラグインです:

1. **`LENS.html`** — 人間が 30 秒で読める 1 ページの要約
2. **`LENS.capsule.md`** — 800-3,600 トークンのコンテキストブロック。AI エージェントが 30 以上の生ファイルを読む **代わりに** 取り込みます
3. **30 のフレームワークアダプター** — 8 つのエコシステムパック (AI アプリ、AI UI、ML コア、サービング、ベクトル DB、エクスペリメント、エンタープライズ、ノートブック)

## インストール

4 つの配布チャネル、お使いのツールに合うものを選択してください:

```bash
# Claude Code / Cowork — projectlens.plugin をチャットにドラッグ&ドロップ
# Cursor / VS Code Copilot / Codex / Gemini CLI — MCP サーバー
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / スクリプト / CI — CLI
pip install projectlens
# コンテキストファイルを読むツール — AGENTS.md モード
projectlens . --install-agents-md
```

## 主な機能

- **適応的な深さ** — T1 (スケッチ) / T2 (アトラス) / T3 (コンパス) を自動選択
- **30 のフレームワークアダプター** — PyTorch、Transformers、LangChain、Pinecone、FastAPI、SQLAlchemy、Vue SFC、Docker Compose など
- **5 つのセッションフック** (Claude Code) — 読み取り重複排除、アクティビティ追跡、選択的注入、出力圧縮、クロスセッションメモリ
- **会話コンパクター** — `/projectlens compact` でセッション中に 8-25k トークンを回収
- **純粋な標準ライブラリ** — ランタイム依存関係ゼロ

## トークン経済

| ステージ | 節約 |
|---|---|
| オリエンテーション | **70-90%** |
| 再読み込み | **~25%** (長いセッション) |
| プロンプトごとの再注入 | **~60%** |
| 中間コンパクション | **8-25k** トークン |

## テスト + パフォーマンス

CI で 527 ユニットテスト + 17 のパフォーマンス/セキュリティ予算が強制されています。500 ファイルのスキャン: **113 ms**。

## ライセンス

MIT。
