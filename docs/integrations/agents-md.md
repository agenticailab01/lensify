# AGENTS.md / CLAUDE.md / GEMINI.md mode

The simplest integration — works with **any** tool that reads a project-root context file.

## What it does

`projectlens . --install-agents-md` runs a scan and writes the capsule into a file at your project root, wrapped in idempotent markers:

```markdown
<!-- projectlens-begin -->

# SUMMARY

Python web API in Python; 312 files, 18,450 LOC.

## ROUTES
- `GET /users`  (api.py:14)
- `POST /users`  (api.py:23)
...

<!-- projectlens-end -->
```

Tools that read this file get the capsule for free, no plugin install needed.

## Which file to write

Different tools read different filenames by convention:

| Tool | Filename |
|---|---|
| Claude Code (legacy mode) | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| Codex / OpenAI | `AGENTS.md` |
| Aider | configurable via `.aider.conf.yml` |
| Antigravity | `AGENTS.md` |
| Generic / multi-tool | `AGENTS.md` (most widely adopted convention) |

Default if you don't specify:

```bash
projectlens . --install-agents-md          # writes AGENTS.md
```

Pick a different file:

```bash
projectlens . --install-agents-md GEMINI.md
projectlens . --install-agents-md CLAUDE.md
projectlens . --install-agents-md docs/CONTEXT.md
```

## Idempotency

Re-running the command replaces only the content between `<!-- projectlens-begin -->` and `<!-- projectlens-end -->`. Anything else you've written into the file (your own instructions, project conventions, contributor notes) is preserved.

## Suggested workflow

1. Maintain your own per-project instructions outside the markers
2. Refresh the projectlens block via a one-liner whenever the codebase changes meaningfully:

```bash
# Add to a Makefile or pre-commit hook
projectlens-refresh:
	projectlens . --install-agents-md
```

3. Tools that read the file get the latest capsule with zero plugin install

## Combining with other channels

`AGENTS.md` mode is **complementary** to the MCP server / CLI / plugin. For example:

- Claude Code users keep the full plugin (hooks + capsule injection)
- Cursor users use the MCP server (re-scan on demand)
- Aider users use `AGENTS.md` mode (cheap, automatic)
- A team can mix: plugin for some devs, AGENTS.md for everyone

The same scan engine powers all of them — keeping the structural picture consistent across the team's tools.
