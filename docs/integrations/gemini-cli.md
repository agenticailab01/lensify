# Gemini CLI

Gemini CLI supports extensions and MCP servers via the standard MCP stdio protocol.

## Configure

Add to your Gemini CLI MCP config (typically `~/.config/gemini-cli/mcp.json`):

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

Restart Gemini CLI.

## Use

```
gemini> use the lensify tool to scan this repo
```

Gemini will call `lensify_scan` and include the returned capsule in its working context.

## Or use AGENTS.md / GEMINI.md mode

Gemini reads `GEMINI.md` by convention. Pre-generate the capsule:

```bash
lensify . --install-agents-md GEMINI.md
```

That writes the capsule directly into `GEMINI.md` wrapped in the lensify markers. Subsequent Gemini sessions will pick it up automatically without an MCP call.

## Combine both

Use AGENTS.md mode for cheap recurring orientation, MCP for on-demand re-scans:

```bash
# Daily refresh
lensify . --install-agents-md GEMINI.md

# Or whenever you want to re-scan inside a session
gemini> @lensify scan
```
