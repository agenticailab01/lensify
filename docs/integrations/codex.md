# Codex (OpenAI)

Codex supports MCP servers via standard MCP stdio. Use the same pattern as Cursor / VS Code.

## Configure

Add to your Codex MCP config:

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/projectlens"
    }
  }
}
```

## Use

The three tools appear under the MCP tools list in Codex:
- `projectlens_scan` — generate the lens
- `projectlens_compact` — mid-session compaction
- `projectlens_stats` — savings report

## What you get

- The capsule is injected into the chat as a tool result
- `LENS.html` written to `projectlens-out/` — open separately
- Codex caches results until you invoke `projectlens_scan` again

## Notes

If you're using Codex CLI without MCP support, fall back to the CLI channel:

```bash
projectlens . --install-agents-md
```

Codex reads `AGENTS.md` by convention, so the capsule will be in context for the next session.
