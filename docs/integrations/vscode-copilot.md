# VS Code Copilot Chat

VS Code supports MCP servers natively (via `mcp.json` in workspace or user settings).

## Configure

Add to your workspace settings (`.vscode/mcp.json`):

```json
{
  "servers": {
    "lensify": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "mcp_server"],
      "cwd": "~/lensify",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/lensify"
      }
    }
  }
}
```

Or for global usage put it in `~/.vscode/mcp.json` and point `cwd` at your local clone.

Reload VS Code (or use the "MCP: Restart Servers" command).

## Use

In Copilot Chat:

```
#lensify scan the current workspace
#lensify compact this session
```

The tools appear in the Copilot Chat tool picker. You can pin them for quick access.

## What you get

- The capsule is injected into the chat as a tool response
- `LENS.html` is written to `lensify-out/` — viewable in VS Code's preview
- `WORKING_CONTEXT.md` for the compactor is ready to be sent into the next session

## Notes

- VS Code's MCP support is in active development. If `#lensify` doesn't show up, verify in `Command Palette → MCP: List Servers`.
- The token savings inside Copilot Chat are smaller than in Claude Code because Copilot doesn't expose UserPromptSubmit hooks for selective injection. The scan + capsule savings still apply.
