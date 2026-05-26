# Cursor

Cursor supports MCP servers via `.cursor/mcp.json` at the project root, or in `~/.cursor/mcp.json` for global setup.

## Install

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
```

(Or `pip install lensify` once published.)

## Configure

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "lensify": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "~/lensify",
      "env": {
        "PYTHONPATH": "/Users/you/lensify"
      }
    }
  }
}
```

Restart Cursor's MCP servers (Settings → MCP → reload).

## Use

In the Cursor chat:

```
@lensify scan this project
@lensify compact
@lensify stats
```

Cursor will call the three exposed tools (`lensify_scan`, `lensify_compact`, `lensify_stats`) and ingest the returned capsule directly into the chat context.

## What you get

- The Markdown capsule appears in the chat
- `LENS.html` is written to `<project>/lensify-out/` — open in the browser
- Cursor caches the result; re-run `@lensify scan` to refresh

## Disable everything

Remove the `lensify` entry from `.cursor/mcp.json`. Cursor's other MCP servers are unaffected.
