# Security policy

## Threat model

Lensify runs **locally inside Claude Code / Cowork** and operates on code the user already trusts enough to open in their editor. It performs:

- Read-only filesystem scans under a user-specified root
- A single optional outbound HTTPS call to `api.anthropic.com` (only when `/lensify compact --llm` is invoked AND `ANTHROPIC_API_KEY` is set)
- Local-only `git` subprocess invocations (`git log`, `git ls-files`) for hotspot detection
- Local-only JSON file writes under `~/.lensify/` (stats) and `<project>/.lensify-memory/` (cross-session memory) — opt-out via env vars

It does **not**:

- Execute or `eval()` source code from the scanned project
- Open shells (`shell=True` is never used)
- Make arbitrary network requests
- Read or transmit files outside the scan root or memory/stats dirs
- Install or modify dependencies
- Perform privileged operations

## What we ship + audit results

| Surface | Risk class | Status |
|---|---|---|
| `subprocess` use | Command injection | Safe — only `git_analyzer.py`, list-args only, 30s timeout, exception-handled |
| `eval` / `exec` / `__import__` | Arbitrary code execution | None in shipped code |
| `pickle` / `marshal` | Deserialization attacks | None — all persistence is JSON |
| Outbound HTTP | Data exfiltration | One hardcoded endpoint (`api.anthropic.com`), opt-in via `--llm` flag + env API key |
| File reads | Path traversal | All paths come from `os.walk(scan_root)` — bounded to the scan root |
| File writes | Out-of-bound writes | Only `<scan_root>/lensify-out/`, `~/.lensify/`, `<scan_root>/.lensify-memory/` |
| API key handling | Credential leakage | Read from env, sent only to `api.anthropic.com`, never logged or persisted |
| User-defined adapters | Arbitrary code execution | **Opt-in only** (see below) |
| Large file DoS | Resource exhaustion | 1 MB per-file read cap; 5 MB notebook cap; 30s git timeout |

## High-attention area — user-defined adapters

Lensify supports per-project adapter drop-ins at `<project>/.lensify/frameworks/*.py`. These files are **imported as Python modules** — if a malicious repo ships an evil adapter, scanning that repo would execute that code inside the agent's environment.

To prevent accidental execution, **user-adapter loading is opt-in**:

```bash
# Set in your shell rc only after deciding you trust the repos you scan
export LENSIFY_USER_ADAPTERS=1
```

When the env var is unset (default), `_load_user_adapters()` returns `[]` without opening the directory. There is no way to enable it from inside a scanned project — the trust decision happens in the user's shell, not in the code being scanned.

If you collaborate on multi-tenant code (e.g. forks from untrusted contributors), leave this env var unset.

## Outbound network usage

Exactly one optional outbound call:

| Endpoint | When | Trigger |
|---|---|---|
| `POST https://api.anthropic.com/v1/messages` | Optional LLM-enhanced summary inside `/lensify compact --llm` | User runs the slash command with `--llm` AND `ANTHROPIC_API_KEY` env var is set |

The request body contains only the session activity summary that the compactor was already going to write to `WORKING_CONTEXT.md` (file paths the user edited, bash commands run, tests results). No file contents are sent.

To disable LLM usage entirely:
- Don't pass `--llm` (the default mode is deterministic)
- OR don't set `ANTHROPIC_API_KEY` (the call short-circuits)

## Data handling

| Data | Location | Lifetime | Opt-out |
|---|---|---|---|
| Lifetime stats counters | `~/.lensify/stats.json` | Permanent until you delete it | `LENSIFY_STATS=0` |
| Cross-session memory | `<project>/.lensify-memory/*.json` | Per-project, capped at 50 entries (LRU) | `LENSIFY_MEMORY=0` |
| Session state | `<project>/lensify-out/state.json` | Per-session only | `LENSIFY_DEDUP=0` (disables all hooks) |
| Capsule + lens artifacts | `<project>/lensify-out/` | Per-project, regenerated each scan | n/a — created only on scan |

Nothing is sent off-device unless you explicitly run `/lensify compact --llm`.

The stats file contains only event counters (e.g. `{"dedup_hits": 42, "edits_tracked": 17, ...}`). No file contents, no commit messages, no PII.

The memory file contains short per-session summaries (active modules, decisions, files touched) that the compactor wrote. Review the contents at any time — they're plain JSON.

## Hook output discipline

All five hooks (`dedup_hook`, `activity_hook`, `inject_hook`, `compress_hook`, `memory_loader`) emit at most 500 tokens per event into the agent's `additionalContext`. This is enforced by the `test_dedup_hook_output_within_envelope` test in the perf harness.

No hook ever emits raw file contents. The dedup hook emits a path + line count summary. The injection hook emits only the *labelled section names* of the capsule, not arbitrary text. Compression replaces long tool outputs with short summaries that include a retrieval handle for the original.

## Reporting a vulnerability

Email `agenticailab01@gmail.com` with subject `[Lensify-security]`. Please **do not file a public GitHub issue** for security reports.

Expected response time: 72 hours.

## Things Lensify is NOT

- Not a security scanner. It surfaces structural code patterns, not vulnerabilities. Don't rely on it for SAST/DAST.
- Not a sandbox. It runs with the same permissions as the agent that invokes it. Don't use it to safely "preview" hostile code.
- Not a license analyzer. It detects framework imports for context, not license obligations.
