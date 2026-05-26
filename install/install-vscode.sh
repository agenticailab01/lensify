#!/usr/bin/env bash
# Install Lensify MCP into VS Code — one command.
set -euo pipefail

# -- path validation: reject shell-special chars that could cause injection
PL_DIR="${LENSIFY_DIR:-$HOME/lensify}"
if [[ "$PL_DIR" =~ [[:space:]\;\|\&\$\`\'\"\<\>] ]]; then
  echo "✗ LENSIFY_DIR contains unsafe characters. Aborting." >&2; exit 1
fi

[[ -d "$PL_DIR" ]] || git clone --depth 1 https://github.com/agenticailab01/lensify "$PL_DIR"

# -- require python3 3.9+
PY="$(command -v python3 || true)"
if [[ -z "$PY" ]]; then
  echo "✗ python3 not found. Install Python 3.9+ first." >&2; exit 1
fi
PY_VER="$("$PY" -c 'import sys; print(sys.version_info >= (3,9))' 2>/dev/null || true)"
if [[ "$PY_VER" != "True" ]]; then
  echo "✗ Python 3.9+ required. Found: $("$PY" --version 2>&1)." >&2; exit 1
fi

# Build JSON safely via Python to avoid shell interpolation issues with paths
CFG_JSON="$("$PY" -c "
import json
print(json.dumps({'name':'lensify','type':'stdio','command':'$PY','args':['-m','mcp_server'],'cwd':'$PL_DIR'}))
")"

code --add-mcp "$CFG_JSON"
echo "✓ VS Code configured. Restart VS Code and ask Copilot Chat: 'scan with lensify'"
