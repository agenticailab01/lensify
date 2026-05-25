# Per-tool integration recipes

ProjectLens ships in **four distribution channels** so it works with virtually any AI coding tool:

| Channel | Tools | Setup |
|---|---|---|
| Native plugin | Claude Code, Cowork | Drop in `projectlens.plugin` |
| MCP server | Cursor, VS Code Copilot Chat, Codex, Gemini CLI, OpenCode, Trae, Kiro, Antigravity | Add a `mcp.json` entry pointing at `python -m mcp_server` |
| CLI | Aider, GitHub Copilot CLI, scripts, CI/CD | `pip install projectlens && projectlens <path>` |
| `AGENTS.md` context file | Anything that auto-reads project context files | `projectlens <path> --install-agents-md` |

Pick the channel matching your tool. Recipes below:

- [Cursor](cursor.md)
- [VS Code Copilot Chat](vscode-copilot.md)
- [Codex](codex.md)
- [Gemini CLI](gemini-cli.md)
- [Aider](aider.md)
- [Generic MCP host](generic-mcp.md)
- [AGENTS.md / CLAUDE.md / GEMINI.md mode](agents-md.md)

## Why this approach

The Claude Code plugin remains untouched (still 201 KB, stdlib-only, drop-in). The MCP server and CLI live as **separate distributions** that reuse the same scan engine — installing them doesn't change the plugin. See `GOVERNANCE.md` for the architectural rationale.

## What ports across all tools

- One-page lens generation
- Token-optimized context capsule (800-3,300 tokens depending on tier)
- All 30 framework adapters
- The conversation compactor (mid-session token reclaim)
- Lifetime stats

## What stays Claude Code-only

- Read dedup hook
- Activity tracking on Edit/Write/Bash
- Selective capsule injection on UserPromptSubmit
- Output compression on Bash/WebFetch
- Cross-session memory loader

These need a hook surface other tools don't expose. The other 70-90% of value (scan + capsule + compactor) is available in every channel.
