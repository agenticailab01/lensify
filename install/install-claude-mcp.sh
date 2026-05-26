#!/usr/bin/env bash
# Install Lensify MCP into Claude Code (in addition to / instead of plugin).
set -euo pipefail
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"
PY="$(command -v python3)"
claude mcp add lensify --scope user --cwd "$PL_DIR" -- "$PY" -m mcp_server
echo "✓ Claude Code MCP configured. Restart Claude Code."
