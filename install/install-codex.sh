#!/usr/bin/env bash
# Install Lensify MCP into OpenAI Codex CLI — one command.
set -euo pipefail
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"
PY="$(command -v python3)"
mkdir -p ~/.codex
cat >> ~/.codex/config.toml <<TOML

[mcp_servers.lensify]
command = "$PY"
args    = ["-m", "mcp_server"]
cwd     = "$PL_DIR"
TOML
echo "✓ Codex configured (~/.codex/config.toml). Restart Codex."
