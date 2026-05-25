# Cursor

Cursor supports MCP servers via `.cursor/mcp.json` at the project root, or in `~/.cursor/mcp.json` for global setup.

## Install

```bash
git clone https://github.com/agenticailab01/projectlens ~/projectlens
```

(Or `pip install projectlens` once published.)

## Configure

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/you/projectlens",
      "env": {
        "PYTHONPATH": "/Users/you/projectlens"
      }
    }
  }
}
```

Restart Cursor's MCP servers (Settings → MCP → reload).

## Use

In the Cursor chat:

```
@projectlens scan this project
@projectlens compact
@projectlens stats
```

Cursor will call the three exposed tools (`projectlens_scan`, `projectlens_compact`, `projectlens_stats`) and ingest the returned capsule directly into the chat context.

## What you get

- The Markdown capsule appears in the chat
- `LENS.html` is written to `<project>/projectlens-out/` — open in the browser
- Cursor caches the result; re-run `@projectlens scan` to refresh

## Disable everything

Remove the `projectlens` entry from `.cursor/mcp.json`. Cursor's other MCP servers are unaffected.
