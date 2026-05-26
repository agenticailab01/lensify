#!/usr/bin/env bash
# Install ProjectLens MCP into VS Code — one command.
set -euo pipefail
PL_DIR="${PROJECTLENS_DIR:-$HOME/projectlens}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/projectlens "$PL_DIR"
PY="$(command -v python3)"
CFG="{\"name\":\"projectlens\",\"type\":\"stdio\",\"command\":\"$PY\",\"args\":[\"-m\",\"mcp_server\"],\"cwd\":\"$PL_DIR\"}"
code --add-mcp "$CFG"
echo "✓ VS Code configured. Restart VS Code and ask Copilot Chat: 'scan with projectlens'"
