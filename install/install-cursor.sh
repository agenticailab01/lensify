#!/usr/bin/env bash
# Install Lensify MCP into Cursor — one command.
# Usage:  bash <(curl -fsSL https://raw.githubusercontent.com/agenticailab01/lensify/main/install/install-cursor.sh)
set -euo pipefail
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"
PY="$(command -v python3)"
cursor mcp add lensify "$PY" -m mcp_server --cwd "$PL_DIR" 2>/dev/null || {
  mkdir -p ~/.cursor
  python3 - "$HOME/.cursor/mcp.json" "$PY" "$PL_DIR" <<'PY'
import json, sys
p, py, c = sys.argv[1:4]
try: cfg = json.load(open(p))
except Exception: cfg = {}
cfg.setdefault("mcpServers", {})["lensify"] = {"command": py, "args": ["-m","mcp_server"], "cwd": c}
open(p,"w").write(json.dumps(cfg, indent=2))
PY
}
echo "✓ Cursor configured. Restart Cursor and try: 'scan this project with Lensify'"
