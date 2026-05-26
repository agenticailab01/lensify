#!/usr/bin/env bash
# Lensify — one-command MCP installer.
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/agenticailab01/lensify/main/install/install-mcp.sh)
#
# Or after cloning:
#   bash install/install-mcp.sh
#
# Auto-detects which AI coding tools you have installed (Cursor, VS Code,
# Claude Code, Gemini CLI, Codex) and offers to register Lensify as
# an MCP server in each one — no manual JSON editing.

set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
SAY() { printf "${BLUE}▸${NC} %s\n" "$*"; }
OK()  { printf "${GREEN}✓${NC} %s\n" "$*"; }
WARN(){ printf "${YELLOW}⚠${NC} %s\n" "$*"; }
ERR() { printf "${RED}✗${NC} %s\n" "$*"; }

# ---------- locate or clone the repo ----------
REPO_URL="https://github.com/agenticailab01/lensify"

# -- path validation: reject chars that could cause injection into configs or shell
_raw_dir="${LENSIFY_DIR:-}"
if [[ -n "$_raw_dir" && "$_raw_dir" =~ [[:space:]\;\|\&\$\`\'\"\<\>] ]]; then
  ERR "LENSIFY_DIR contains unsafe characters. Aborting."
  exit 1
fi

if [[ -d "${LENSIFY_DIR:-}" ]]; then
  PL_DIR="$LENSIFY_DIR"
elif [[ -d "$HOME/lensify" ]]; then
  PL_DIR="$HOME/lensify"
elif [[ -d "$HOME/Documents/GitHub/Claude/Lensify" ]]; then
  PL_DIR="$HOME/Documents/GitHub/Claude/Lensify"
else
  SAY "Cloning Lensify to $HOME/lensify"
  git clone --depth 1 "$REPO_URL" "$HOME/lensify"
  PL_DIR="$HOME/lensify"
fi
OK "Lensify repo at: $PL_DIR"

# Quick sanity check — does mcp_server/__main__.py exist?
if [[ ! -f "$PL_DIR/mcp_server/__main__.py" ]]; then
  ERR "$PL_DIR doesn't look like a Lensify checkout (no mcp_server/__main__.py)"
  exit 1
fi

# Resolve python3 absolute path so tools don't fail with "python3: command not found"
PYTHON_BIN="$(command -v python3 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  ERR "python3 not found on PATH. Install Python 3.9+ first."
  exit 1
fi
PY_VER="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info >= (3,9))' 2>/dev/null || true)"
if [[ "$PY_VER" != "True" ]]; then
  ERR "Python 3.9+ required. Found: $("$PYTHON_BIN" --version 2>&1)."
  exit 1
fi
OK "Using python at: $PYTHON_BIN"

# ---------- detect tools ----------
declare -a AVAILABLE=()
has() { command -v "$1" >/dev/null 2>&1; }
has cursor   && AVAILABLE+=("cursor")
has code     && AVAILABLE+=("vscode")
has claude   && AVAILABLE+=("claude")
has gemini   && AVAILABLE+=("gemini")
has codex    && AVAILABLE+=("codex")

if [[ ${#AVAILABLE[@]} -eq 0 ]]; then
  WARN "No supported tools detected on PATH (cursor / code / claude / gemini / codex)"
  WARN "Install Lensify as a plugin instead — see USER-INSTALL.md"
  exit 0
fi

echo
SAY "Detected tools: ${AVAILABLE[*]}"
echo "Which would you like to configure?"
PS3="Select (number, comma-separated, or 'all'): "
select_targets() {
  read -r -p "$PS3" input
  if [[ "$input" == "all" ]]; then
    printf "%s\n" "${AVAILABLE[@]}"
  else
    # split by comma/space
    IFS=', ' read -ra picks <<< "$input"
    for p in "${picks[@]}"; do
      if [[ "$p" =~ ^[0-9]+$ ]]; then
        idx=$((p-1))
        [[ $idx -ge 0 && $idx -lt ${#AVAILABLE[@]} ]] && echo "${AVAILABLE[$idx]}"
      else
        # name match
        for t in "${AVAILABLE[@]}"; do [[ "$t" == "$p" ]] && echo "$t"; done
      fi
    done
  fi
}
for i in "${!AVAILABLE[@]}"; do
  printf "  %d) %s\n" $((i+1)) "${AVAILABLE[$i]}"
done
mapfile -t TARGETS < <(select_targets)

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  ERR "No valid selection. Exiting."
  exit 1
fi

# ---------- per-tool installers ----------
install_cursor() {
  SAY "Configuring Cursor..."
  # Cursor 0.42+ exposes: cursor mcp add <name> <command> [args...] [--cwd path]
  if cursor mcp add lensify "$PYTHON_BIN" "-m" "mcp_server" --cwd "$PL_DIR" 2>/dev/null; then
    OK "Cursor configured."
    return
  fi
  # Fallback: write the JSON config directly (atomic via temp file)
  CFG="$HOME/.cursor/mcp.json"
  mkdir -p "$(dirname "$CFG")"
  python3 - "$CFG" "$PYTHON_BIN" "$PL_DIR" <<'PY'
import json, sys, os, tempfile
cfg_path, py, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path) as f: cfg = json.load(f)
except Exception: cfg = {}
cfg.setdefault("mcpServers", {})["lensify"] = {"command": py, "args": ["-m", "mcp_server"], "cwd": cwd}
dir_ = os.path.dirname(os.path.abspath(cfg_path))
fd, tmp = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(fd, "w") as fh: fh.write(json.dumps(cfg, indent=2))
    os.replace(tmp, cfg_path)
except Exception:
    try: os.unlink(tmp)
    except OSError: pass
    raise
print(f"  wrote {cfg_path}")
PY
  OK "Cursor config updated (~/.cursor/mcp.json). Restart Cursor."
}

install_vscode() {
  SAY "Configuring VS Code..."
  # code --add-mcp '{...}'  (VS Code 1.93+)
  CFG_JSON=$(cat <<JSON
{"name":"lensify","type":"stdio","command":"$PYTHON_BIN","args":["-m","mcp_server"],"cwd":"$PL_DIR"}
JSON
)
  if code --add-mcp "$CFG_JSON" 2>/dev/null; then
    OK "VS Code configured (CLI)."
    return
  fi
  WARN "code --add-mcp not available — writing .vscode/mcp.json fallback (workspace-scoped)"
  CFG="${VSCODE_WORKSPACE:-$PWD}/.vscode/mcp.json"
  mkdir -p "$(dirname "$CFG")"
  python3 - "$CFG" "$PYTHON_BIN" "$PL_DIR" <<'PY'
import json, sys, os, tempfile
cfg_path, py, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path) as f: cfg = json.load(f)
except Exception: cfg = {}
cfg.setdefault("servers", {})["lensify"] = {"type": "stdio", "command": py, "args": ["-m", "mcp_server"], "cwd": cwd}
dir_ = os.path.dirname(os.path.abspath(cfg_path))
fd, tmp = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(fd, "w") as fh: fh.write(json.dumps(cfg, indent=2))
    os.replace(tmp, cfg_path)
except Exception:
    try: os.unlink(tmp)
    except OSError: pass
    raise
print(f"  wrote {cfg_path}")
PY
  OK "VS Code config updated. Restart VS Code."
}

install_claude() {
  SAY "Configuring Claude Code (MCP)..."
  # claude mcp add <name> -- <command> [args...]
  if claude mcp add lensify --scope user --cwd "$PL_DIR" -- "$PYTHON_BIN" -m mcp_server 2>/dev/null; then
    OK "Claude Code MCP configured."
    return
  fi
  WARN "claude mcp add not available — falling back to direct config"
  CFG="$HOME/.claude.json"
  python3 - "$CFG" "$PYTHON_BIN" "$PL_DIR" <<'PY'
import json, sys, os, tempfile
cfg_path, py, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path) as f: cfg = json.load(f)
except Exception: cfg = {}
cfg.setdefault("mcpServers", {})["lensify"] = {"command": py, "args": ["-m", "mcp_server"], "cwd": cwd}
dir_ = os.path.dirname(os.path.abspath(cfg_path))
fd, tmp = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(fd, "w") as fh: fh.write(json.dumps(cfg, indent=2))
    os.replace(tmp, cfg_path)
except Exception:
    try: os.unlink(tmp)
    except OSError: pass
    raise
print(f"  wrote {cfg_path}")
PY
  OK "Claude Code config updated. Restart Claude Code."
}

install_gemini() {
  SAY "Configuring Gemini CLI..."
  if gemini mcp add lensify "$PYTHON_BIN" -m mcp_server --cwd "$PL_DIR" 2>/dev/null; then
    OK "Gemini CLI configured."
    return
  fi
  CFG="$HOME/.gemini/settings.json"
  mkdir -p "$(dirname "$CFG")"
  python3 - "$CFG" "$PYTHON_BIN" "$PL_DIR" <<'PY'
import json, sys, os, tempfile
cfg_path, py, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path) as f: cfg = json.load(f)
except Exception: cfg = {}
cfg.setdefault("mcpServers", {})["lensify"] = {"command": py, "args": ["-m", "mcp_server"], "cwd": cwd}
dir_ = os.path.dirname(os.path.abspath(cfg_path))
fd, tmp = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(fd, "w") as fh: fh.write(json.dumps(cfg, indent=2))
    os.replace(tmp, cfg_path)
except Exception:
    try: os.unlink(tmp)
    except OSError: pass
    raise
print(f"  wrote {cfg_path}")
PY
  OK "Gemini config updated. Restart Gemini CLI."
}

install_codex() {
  SAY "Configuring OpenAI Codex CLI..."
  CFG="$HOME/.codex/config.toml"
  mkdir -p "$(dirname "$CFG")"
  # guard against duplicate entries; use atomic Python write to handle path chars safely
  if grep -q '\[mcp_servers\.lensify\]' "$CFG" 2>/dev/null; then
    OK "Lensify already present in $CFG — skipping duplicate entry."
    return
  fi
  python3 - "$CFG" "$PYTHON_BIN" "$PL_DIR" <<'PY'
import sys, os, tempfile, json
cfg_path, py_bin, cwd = sys.argv[1], sys.argv[2], sys.argv[3]
existing = ""
if os.path.exists(cfg_path):
    with open(cfg_path) as f: existing = f.read()
entry = (
    "\n[mcp_servers.lensify]\n"
    f"command = {json.dumps(py_bin)}\n"
    'args    = ["-m", "mcp_server"]\n'
    f"cwd     = {json.dumps(cwd)}\n"
)
dir_ = os.path.dirname(os.path.abspath(cfg_path))
fd, tmp = tempfile.mkstemp(dir=dir_)
try:
    with os.fdopen(fd, "w") as fh: fh.write(existing + entry)
    os.replace(tmp, cfg_path)
except Exception:
    try: os.unlink(tmp)
    except OSError: pass
    raise
print(f"  wrote {cfg_path}")
PY
  OK "Codex CLI config updated ($CFG). Restart Codex."
}

# ---------- run selected installers ----------
for t in "${TARGETS[@]}"; do
  echo
  case "$t" in
    cursor) install_cursor ;;
    vscode) install_vscode ;;
    claude) install_claude ;;
    gemini) install_gemini ;;
    codex)  install_codex  ;;
  esac
done

echo
OK "Done. Restart the configured tools and ask your agent: \"scan this project with Lensify\""
