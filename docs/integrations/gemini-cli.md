# Gemini CLI

Gemini CLI supports extensions and MCP servers via the standard MCP stdio protocol.

## Configure

Add to your Gemini CLI MCP config (typically `~/.config/gemini-cli/mcp.json`):

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

Restart Gemini CLI.

## Use

```
gemini> use the projectlens tool to scan this repo
```

Gemini will call `projectlens_scan` and include the returned capsule in its working context.

## Or use AGENTS.md / GEMINI.md mode

Gemini reads `GEMINI.md` by convention. Pre-generate the capsule:

```bash
projectlens . --install-agents-md GEMINI.md
```

That writes the capsule directly into `GEMINI.md` wrapped in the projectlens markers. Subsequent Gemini sessions will pick it up automatically without an MCP call.

## Combine both

Use AGENTS.md mode for cheap recurring orientation, MCP for on-demand re-scans:

```bash
# Daily refresh
projectlens . --install-agents-md GEMINI.md

# Or whenever you want to re-scan inside a session
gemini> @projectlens scan
```
