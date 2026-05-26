#!/usr/bin/env bash
# Install ProjectLens MCP into Gemini CLI — one command.
set -euo pipefail
PL_DIR="${PROJECTLENS_DIR:-$HOME/projectlens}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/projectlens "$PL_DIR"
PY="$(command -v python3)"
gemini mcp add projectlens "$PY" -m mcp_server --cwd "$PL_DIR"
echo "✓ Gemini CLI configured."
