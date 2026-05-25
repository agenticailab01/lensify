# ProjectLens

> 适用于任何代码库的单次扫描自适应项目透镜 + 令牌优化上下文胶囊。为 AI 编码助手节省 70-90% 的方向定位令牌。

[English](../../README.md) · **简体中文** · [日本語](README.ja.md) · [한국어](README.ko.md)

## 是什么

ProjectLens 是一个插件,通过 **一次扫描**(50-150 毫秒)将任何代码库转换为:

1. **`LENS.html`** — 单页摘要,人类 30 秒可读
2. **`LENS.capsule.md`** — 800-3,600 个令牌的上下文块,AI 代理可摄取此块,**而非** 阅读 30 多个原始文件
3. **30 个框架适配器** — 涵盖 8 个生态系统包:AI 应用、AI UI、ML 核心、推理服务、向量数据库、实验追踪、企业级、笔记本

## 安装

四个分发渠道,选择适合您工具的:

```bash
# Claude Code / Cowork —— 拖放 projectlens.plugin 到聊天中
# Cursor / VS Code Copilot / Codex / Gemini CLI —— MCP 服务器
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / 脚本 / CI —— CLI
pip install projectlens
# 任何读取上下文文件的工具 —— AGENTS.md 模式
projectlens . --install-agents-md
```

详细安装步骤请见 [完整 README](../../README.md#quick-start)。

## 主要功能

- **自适应深度** — 自动选择 T1 (简略) / T2 (地图) / T3 (罗盘)
- **30 个框架适配器** — PyTorch、Transformers、LangChain、Pinecone、FastAPI、SQLAlchemy、Vue SFC、Docker Compose 等
- **5 个会话钩子**(Claude Code) — 读取去重、活动跟踪、选择性注入、输出压缩、跨会话内存
- **对话压缩器** — `/projectlens compact` 在会话中期回收 8-25k 令牌
- **纯标准库** — 零运行时依赖

## 令牌经济学

| 阶段 | 节省 |
|---|---|
| 方向定位 | **70-90%** |
| 重复读取 | **~25%** (长会话) |
| 每提示重新注入 | **~60%** |
| 中期压缩 | **8-25k** 令牌 |

## 测试 + 性能

527 单元测试 + 17 个性能/安全预算在 CI 中强制执行。500 个文件扫描:**113 毫秒**。

## 许可证

MIT。详情请见 [LICENSE](../../LICENSE)。
