#!/usr/bin/env bash
# Install ProjectLens MCP into OpenAI Codex CLI — one command.
set -euo pipefail
PL_DIR="${PROJECTLENS_DIR:-$HOME/projectlens}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/projectlens "$PL_DIR"
PY="$(command -v python3)"
mkdir -p ~/.codex
TOML_FILE="$HOME/.codex/config.toml"
if grep -q '\[mcp_servers.projectlens\]' "$TOML_FILE" 2>/dev/null; then
  echo "✓ Codex already configured (skipping duplicate). Restart Codex."
else
  cat >> "$TOML_FILE" <<TOML

[mcp_servers.projectlens]
command = "$PY"
args    = ["-m", "mcp_server"]
cwd     = "$PL_DIR"
TOML
  echo "✓ Codex configured ($TOML_FILE). Restart Codex."
fi
