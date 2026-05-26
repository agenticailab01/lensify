# Codex (OpenAI)

Codex supports MCP servers via standard MCP stdio. Use the same pattern as Cursor / VS Code.

## Configure

Add to your Codex MCP config:

```json
{
  "mcpServers": {
    "lensify": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "~/lensify"
    }
  }
}
```

## Use

The three tools appear under the MCP tools list in Codex:
- `lensify_scan` — generate the lens
- `lensify_compact` — mid-session compaction
- `lensify_stats` — savings report

## What you get

- The capsule is injected into the chat as a tool result
- `LENS.html` written to `lensify-out/` — open separately
- Codex caches results until you invoke `lensify_scan` again

## Notes

If you're using Codex CLI without MCP support, fall back to the CLI channel:

```bash
lensify . --install-agents-md
```

Codex reads `AGENTS.md` by convention, so the capsule will be in context for the next session.
