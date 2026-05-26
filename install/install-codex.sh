#!/usr/bin/env bash
# Install Lensify MCP into OpenAI Codex CLI — one command.
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

mkdir -p ~/.codex
CFG="$HOME/.codex/config.toml"

# -- guard against duplicate entries on re-run
if grep -q '\[mcp_servers\.lensify\]' "$CFG" 2>/dev/null; then
  echo "✓ Lensify already present in $CFG — skipping duplicate entry."
else
  # atomic write via Python: avoids TOML injection through path chars and partial writes
  "$PY" - "$CFG" "$PY" "$PL_DIR" <<'PY'
import sys, os, tempfile, json

cfg_path, py_bin, cwd = sys.argv[1], sys.argv[2], sys.argv[3]

existing = ""
if os.path.exists(cfg_path):
    with open(cfg_path) as f:
        existing = f.read()

entry = (
    "\n[mcp_servers.lensify]\n"
    f"command = {json.dumps(py_bin)}\n"
    f'args    = ["-m", "mcp_server"]\n'
    f"cwd     = {json.dumps(cwd)}\n"
)

dir_ = os.path.dirname(os.path.abspath(cfg_path))
tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(tmp_fd, "w") as fh:
        fh.write(existing + entry)
    os.replace(tmp_path, cfg_path)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
PY
fi

echo "✓ Codex configured (~/.codex/config.toml). Restart Codex."
