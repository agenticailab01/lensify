#!/usr/bin/env bash
# Install ProjectLens MCP into Claude Code (in addition to / instead of plugin).
set -euo pipefail
PL_DIR="${PROJECTLENS_DIR:-$HOME/projectlens}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/projectlens "$PL_DIR"
PY="$(command -v python3)"
claude mcp add projectlens --scope user --cwd "$PL_DIR" -- "$PY" -m mcp_server
echo "✓ Claude Code MCP configured. Restart Claude Code."
