# Lensify install — security stance

We deliberately avoid `curl | bash`-style installers as the recommended path.
That pattern fetches a remote script and executes it in one step, with no
opportunity to review what runs on your machine. It's a known supply-chain
attack vector, modern AI coding assistants reject it, and security-conscious
operators have policies that block it.

## What we use instead

| Channel | What runs on your machine | Why it's safe |
|---|---|---|
| Claude Code CLI plugin | `/plugin marketplace add` + `/plugin install` | Built into Claude Code. Anthropic-signed code path. No remote script. |
| Cowork plugin | Drag-drop a `lensify.plugin` file you downloaded yourself | You explicitly downloaded and approved the file. Cowork validates it. |
| MCP (Cursor / VS Code / Claude Code / Gemini) | `cursor mcp add` / `code --add-mcp` / `claude mcp add` / `gemini mcp add` | Tool-native commands documented by the tool vendor. They write to known config files. |
| Manual config | Edit `~/.cursor/mcp.json` etc. directly | You see and approve every byte before it lands. |

## The convenience scripts in `install/`

The `install/install-*.sh` scripts in this repo are an optional accelerator
for users who configure many tools at once. **They're not the default install
path** — the README points at the two-command native install first.

If you want to use them, the safe pattern is:

```bash
# 1. Clone the repo (so you have the script locally, not remote)
git clone https://github.com/agenticailab01/lensify ~/lensify
cd ~/lensify

# 2. Read the script — they're ~20 lines each, plain bash
cat install/install-vscode.sh

# 3. Run it once you're satisfied
bash install/install-vscode.sh
```

The scripts themselves only:
- Check `python3` is on `$PATH`
- Resolve absolute path of the cloned repo
- Run the tool's own `mcp add` command (or write its own config file)

No network calls (other than the original git clone you already approved),
no telemetry, no privilege escalation. The source is the proof.

## Reporting concerns

If you spot anything in our install path that doesn't match this stance,
open an issue or email `agenticailab01@gmail.com`. We'll fix it the same
day.
