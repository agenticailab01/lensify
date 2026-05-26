#!/usr/bin/env bash
# Install Lensify MCP into Claude Code (in addition to / instead of plugin).
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

claude mcp add lensify --scope user --cwd "$PL_DIR" -- "$PY" -m mcp_server
echo "✓ Claude Code MCP configured. Restart Claude Code."
