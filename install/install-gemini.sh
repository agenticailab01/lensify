#!/usr/bin/env bash
# Install Lensify MCP into Gemini CLI — one command.
set -euo pipefail
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"
PY="$(command -v python3)"
gemini mcp add lensify "$PY" -m mcp_server --cwd "$PL_DIR"
echo "✓ Gemini CLI configured."
