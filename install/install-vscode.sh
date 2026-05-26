#!/usr/bin/env bash
# Install Lensify MCP into VS Code — one command.
set -euo pipefail
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"
PY="$(command -v python3)"
CFG="{\"name\":\"lensify\",\"type\":\"stdio\",\"command\":\"$PY\",\"args\":[\"-m\",\"mcp_server\"],\"cwd\":\"$PL_DIR\"}"
code --add-mcp "$CFG"
echo "✓ VS Code configured. Restart VS Code and ask Copilot Chat: 'scan with lensify'"
