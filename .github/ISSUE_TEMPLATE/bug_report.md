---
name: Bug report
about: A correctness or performance issue with shipped code
title: '[bug] '
labels: bug
---

## What happened

A clear description of the bug.

## Reproduction

Minimal steps to reproduce:

```bash
# Commands you ran
```

If the bug is in an adapter, include a tiny project that triggers it (5-10 lines of code is usually enough).

## Expected vs actual

- **Expected:** what you thought would happen
- **Actual:** what happened instead

## Environment

- ProjectLens version: (run `projectlens --version` or check `.claude-plugin/plugin.json`)
- Channel: (plugin / MCP server / CLI / AGENTS.md mode)
- Python: (output of `python3 --version`)
- OS: (macOS / Linux / Windows)
- Host tool: (Claude Code / Cowork / Cursor / VS Code / Codex / …)

## Additional context

Anything else — logs, perf output, screenshots, etc.
