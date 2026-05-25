# ProjectLens

> 適用於任何程式碼庫的單次掃描自適應專案透鏡 + 令牌最佳化上下文膠囊。為 AI 編碼助手節省 70-90% 的方向定位令牌。

[English](../../README.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [日本語](README.ja.md)

## 是什麼

ProjectLens 是一個外掛,透過 **一次掃描**(50-150 毫秒)將任何程式碼庫轉換為:

1. **`LENS.html`** — 單頁摘要,人類 30 秒可讀
2. **`LENS.capsule.md`** — 800-3,600 個令牌的上下文塊,AI 代理可攝取此塊,**而非** 閱讀 30 多個原始檔案
3. **30 個框架介面卡** — 涵蓋 8 個生態系統套件

## 安裝

```bash
# Claude Code / Cowork —— 拖放 projectlens.plugin 到聊天中
# Cursor / VS Code / Codex / Gemini CLI —— MCP 伺服器
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / 腳本 / CI —— CLI
pip install projectlens
# 任何讀取上下文檔案的工具 —— AGENTS.md 模式
projectlens . --install-agents-md
```

## 主要功能

- **自適應深度** (T1/T2/T3)
- **30 個框架介面卡** — PyTorch、LangChain、FastAPI、Pinecone 等
- **5 個會話掛鉤** (Claude Code)
- **對話壓縮器** — 中期回收 8-25k 令牌
- **純標準函式庫** — 零執行時相依性

## 授權

MIT。
