# Install Lensify — pick one of three paths

Every path takes under a minute. **No path uses `curl | bash` or executes
remote scripts blind** — every command is one you type yourself and can
review beforehand.

---

## Path A · Claude Code (terminal CLI) — 30 seconds

Type these inside the Claude Code chat window:

```
/plugin marketplace add agenticailab01/lensify
/plugin install lensify@lensify
```

These are Claude Code's own built-in commands. The first registers the GitHub repo as a plugin marketplace (works because the repo has `.claude-plugin/marketplace.json`). The second installs the plugin from that marketplace.

To uninstall later: `/plugin uninstall lensify@lensify`

---

## Path B · Cowork (desktop chat) — drag and drop

1. Open <https://github.com/agenticailab01/lensify/releases>.
2. Download the latest `lensify.plugin` file.
3. Drag it into the Cowork chat window.
4. Click **Save plugin**.
5. Restart the conversation. You'll see `Lensify dedup is active`.

To uninstall: Cowork settings → Plugins → Lensify → Remove.

---

## Path C · Cursor / VS Code / Codex / Gemini CLI (MCP) — two transparent commands

No `curl | bash`. No remote scripts. Two commands you type yourself.

### Step 1 — clone the repo (one-time, ~200 KB pure Python)

```bash
git clone https://github.com/agenticailab01/lensify ~/lensify
```

### Step 2 — register the MCP server with your tool

Pick the line that matches your tool — **these are the tool's own commands**, not anything from us:

```bash
# Cursor — uses cursor's built-in MCP-add command
cursor mcp add lensify python3 -m mcp_server --cwd ~/lensify

# VS Code — uses code's built-in --add-mcp flag
code --add-mcp '{"name":"lensify","type":"stdio","command":"python3","args":["-m","mcp_server"],"cwd":"'"$HOME"'/lensify"}'

# Claude Code MCP — uses claude's built-in mcp add subcommand
claude mcp add lensify --scope user --cwd ~/lensify -- python3 -m mcp_server

# Gemini CLI — uses gemini's built-in mcp add subcommand
gemini mcp add lensify python3 -m mcp_server --cwd ~/lensify
```

For OpenAI Codex (no `mcp add` subcommand yet), append this to `~/.codex/config.toml`:

```toml
[mcp_servers.lensify]
command = "python3"
args    = ["-m", "mcp_server"]
cwd     = "/Users/you/lensify"
```

Restart the tool. Three new tools appear: `lensify_scan`, `lensify_compact`, `lensify_stats`.

### Prefer one-click? (Cursor / VS Code)

Click a badge — your editor opens its native MCP-install dialog. Still requires Step 1 (clone).

[![Install in Cursor](https://img.shields.io/badge/Install%20in-Cursor-000000?style=for-the-badge&logo=cursor)](cursor://anysphere.cursor-deeplink/mcp/install?name=lensify&config=eyJjb21tYW5kIjogInB5dGhvbjMiLCAiYXJncyI6IFsiLW0iLCAibWNwX3NlcnZlciJdLCAiY3dkIjogIiRIT01FL2xlbnNpZnkifQ)
[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode)](vscode:mcp/install?%7B%22name%22%3A%22lensify%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22python3%22%2C%22args%22%3A%5B%22-m%22%2C%22mcp_server%22%5D%2C%22cwd%22%3A%22%24HOME%2Flensify%22%7D)

To uninstall: re-run the same `cursor/code/claude/gemini mcp` command with `remove` instead of `add`, or delete the `lensify` entry from the tool's MCP config file.

---

## Updating to the latest version

Pick the section that matches how you installed.

### Claude Code plugin (Path A)

Run these two lines inside the Claude Code chat window:

```text
/plugin uninstall lensify@lensify
/plugin install lensify@lensify
```

This pulls the latest code from the marketplace and refreshes the local cache. Start a new conversation to activate the update.

### Cowork plugin (Path B)

1. Download the latest `lensify.plugin` from the [Releases page](https://github.com/agenticailab01/lensify/releases).
2. Drag it into the Cowork chat window and click **Save plugin** — it overwrites the installed version.
3. Restart the conversation.

### MCP / git clone (Path C)

```bash
cd ~/lensify
git pull
```

Then fully restart your tool (Cursor, VS Code, Codex, Gemini CLI). No re-registration needed — the MCP config already points to `~/lensify`.

### pip CLI

```bash
pip install --upgrade lensify
```

---

## Why we don't use `curl | bash`

`bash <(curl -fsSL https://...)` fetches a script and runs it in one step
with no chance to review the contents. It's a known supply-chain attack
pattern — modern AI assistants flag it, security-conscious users refuse
it, and they're both right. We use only:

1. **Tool-native CLI commands** (Path A's `/plugin install`, Path C's `cursor mcp add` / `code --add-mcp` etc.) — documented by the tool vendor, signed-off by vendor security policy.
2. **A clone + tool-native sequence** (Path C). You see the source code before anything runs on your machine.

The `install/*.sh` scripts in the repo are an **optional convenience** for users who set up many tools at once. The README explicitly tells you to read them before running.

---

## Verifying it worked

After install, run one of these:

- **Claude Code / Cowork:** `/lensify stats` — should print lifetime savings.
- **MCP tools:** ask the agent *"show my lensify stats"*.

If you see numbers, you're good.

---

## Which path should I pick?

| Your setup | Path |
|---|---|
| Using Claude Code as your daily driver | **A** (all 5 hooks active) |
| Using Cowork desktop app | **B** (all 5 hooks active) |
| Using Cursor, VS Code, or any non-Anthropic tool | **C** (3 tools, no hooks) |
| Using more than one tool | **A or B** for the primary, **C** for the others |
