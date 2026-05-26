#!/usr/bin/env bash
# Install Lensify MCP into Cursor — one command.
# Usage:  bash <(curl -fsSL https://raw.githubusercontent.com/agenticailab01/lensify/main/install/install-cursor.sh)
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

cursor mcp add lensify "$PY" -m mcp_server --cwd "$PL_DIR" 2>/dev/null || {
  mkdir -p ~/.cursor
  # atomic JSON write: temp file + os.replace prevents partial-write corruption
  "$PY" - "$HOME/.cursor/mcp.json" "$PY" "$PL_DIR" <<'PY'
import json, sys, os, tempfile

cfg_path, py_bin, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

cfg.setdefault("mcpServers", {})["lensify"] = {
    "command": py_bin, "args": ["-m", "mcp_server"], "cwd": cwd
}

dir_ = os.path.dirname(os.path.abspath(cfg_path))
tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(tmp_fd, "w") as fh:
        fh.write(json.dumps(cfg, indent=2))
    os.replace(tmp_path, cfg_path)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
PY
}

echo "✓ Cursor configured. Restart Cursor and try: 'scan this project with Lensify'"
