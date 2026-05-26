# Governance

## Purpose + scope

Lensify exists to **reduce orientation tokens** and **summarise project structure** for AI coding agents. Everything in the codebase serves that purpose. We don't accept changes that go beyond it.

In particular, the project explicitly does **not** intend to be:

- A code-execution platform
- A network proxy / tunnel / scraper
- A credential or secret harvester
- A vulnerability scanner
- An automation surface for sending mail, posting to chat, triggering deploys, etc.
- A way to bypass other tools' permission models

Any pull request that adds capabilities along these lines will be rejected. The plugin's value depends on it being a **read-only, locally-scoped, predictable** tool.

## Acceptable contributions

Contributions are welcomed in these categories:

1. **New framework adapters** — see `references/adapter-sdk.md`. Adapters must be small (~80-120 LOC), follow the R1-R5 perf rules, ship with tests, and detect frameworks the contributor uses in production.
2. **Bug fixes** — any correctness/perf issue in shipped adapters or hooks. Include a test that fails before your fix.
3. **Doc + DX improvements** — README, CHANGELOG, references, error messages.
4. **Performance work** — anything that improves scan time or token economy without weakening safety.

## Unacceptable contributions

Listed concretely so reviewers have a sharp line to point at:

- Anything that introduces `exec()`, `eval()`, `pickle.loads()`, `__import__()` on user data
- Anything that uses `shell=True`, `os.system()`, or builds shell strings from user input
- Outbound HTTP to anywhere other than `api.anthropic.com` (and even that stays inside `llm_client.py`)
- Auto-loading mechanisms that run third-party code without an explicit user opt-in
- Telemetry or analytics that send data off-device
- Adapters that ship hardcoded API keys, OAuth tokens, or other credentials
- Adapters whose output includes copyrighted source verbatim instead of structural summaries
- Adapters whose detection logic is so generic it would trigger on unrelated projects (e.g. matching `from utils import *`)
- Anything described as "scraping," "scanning the network," "monitoring," "intercepting," "exfiltrating"

## Anti-spam + anti-abuse measures

Per-event safeguards built into the codebase:

| Risk | Mitigation |
|---|---|
| Hook chatter overwhelms agent | 500-token envelope per event (perf test enforced) |
| Capsule output bloats the prompt | Per-tier total token budgets enforced by `test_capsule_token_budget_unchanged` |
| Adapter floods capsule with entries | `ABSOLUTE_MAX_ENTRIES = 50` per adapter, capped by base class |
| Repeated reads burn tokens | Dedup hook collapses re-reads to a single flag |
| Huge files block scans | 1 MB per-file read cap (`LENSIFY_MAX_READ_BYTES`), 5 MB notebook cap |
| Long git history blocks scans | 30-second subprocess timeout |
| Adapter exception kills scan | Every adapter call is wrapped in `try/except` — a broken adapter never breaks the scan |
| Untrusted user adapters auto-run | Off by default; requires `LENSIFY_USER_ADAPTERS=1` in user's shell |

## User rights + transparency

Every persistent surface has a documented opt-out env var:

```bash
LENSIFY_DEDUP=0          # turn off ALL hooks
LENSIFY_STATS=0          # turn off lifetime stats
LENSIFY_MEMORY=0         # turn off cross-session memory
LENSIFY_COMPRESS_OUTPUT=0 # turn off output compression
LENSIFY_USER_ADAPTERS=1  # opt IN to user-defined adapters (off by default)
LENSIFY_MAX_READ_BYTES=N # change per-file read cap
LENSIFY_STATS_HOME=path  # change where stats live (tests / power users)
```

All persistent files are plain JSON / Markdown — auditable, deletable, no databases or binary formats.

`/lensify stats` shows what's accumulated locally. Delete `~/.lensify/` and `<project>/.lensify-memory/` to wipe everything.

## Legal + ethical use

Lensify is intended for use on code its operator has the right to view. Don't use it to:

- Survey code you obtained without authorisation
- Reverse-engineer products in violation of their licenses
- Extract trade secrets from a partner's codebase you happen to have read access to
- Aggregate scan results across customers without their consent

These are user responsibilities — the tool itself has no way to enforce them, but the project's stance is unambiguous.

## License

MIT. See `LICENSE` at the repository root. By contributing, you agree your contributions are licensed under MIT as well.

## Maintainers

Sachin Patil (`agenticailab01@gmail.com`).

## Project status

Active development. Stable feature surface as of v0.14.0. Breaking changes will bump the major version (1.0.0 is the next planned milestone).
