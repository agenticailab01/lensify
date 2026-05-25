# Generic MCP host

Any MCP-compatible tool can use ProjectLens via the stdio server. This recipe is the generic baseline — adapt to your tool's specific config format.

## Server invocation

```bash
python3 -m mcp_server
```

Reads JSON-RPC 2.0 requests from stdin, writes responses to stdout (newline-delimited JSON). MCP spec version targeted: `2024-11-05`.

## Tools exposed

| Tool | Description | Required args |
|---|---|---|
| `projectlens_scan` | Generate lens + capsule for a project | `path` |
| `projectlens_compact` | Generate WORKING_CONTEXT.md from session state | `path` |
| `projectlens_stats` | Lifetime savings report | (none) |

## Optional args

For `projectlens_scan`:
- `tier`: `"auto"` (default) / `"T1"` / `"T2"` / `"T3"`
- `capsule_only`: skip HTML, write only the Markdown capsule
- `ast_only`: deterministic mode — no LLM enrichment of narrative
- `no_git`: skip git hotspot analysis (faster)
- `output_dir`: override default `<project>/projectlens-out/`

For `projectlens_compact`:
- `llm`: enable Haiku-enhanced narrative (requires `ANTHROPIC_API_KEY`)
- `output_dir`

## Generic config snippet

Most MCP hosts accept some variant of:

```json
{
  "mcpServers": {
    "projectlens": {
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "/absolute/path/to/projectlens"
    }
  }
}
```

The exact location of this file varies by tool:
- Cursor: `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global)
- VS Code: `.vscode/mcp.json` or workspace settings
- Codex: depends on platform
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- Gemini CLI: `~/.config/gemini-cli/mcp.json`

## Testing the server by hand

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | python3 -m mcp_server
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python3 -m mcp_server
```

You should see well-formed JSON-RPC responses on stdout.

## Troubleshooting

**Server doesn't start.** Run `python3 -m mcp_server` interactively — any startup error prints to stderr.

**Tools don't appear in the host.** Confirm the host actually loads MCP servers (check its logs / status panel). Send `tools/list` manually as above to verify the server is responsive.

**Tools call returns an error.** The error response includes a `data` field with up to 2 KB of traceback — usually enough to diagnose.

## Disabling

Remove the `projectlens` entry from your tool's MCP config. The ProjectLens server is stateless across hosts.
