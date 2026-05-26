# Contributing to Lensify

Thanks for thinking about contributing. Lensify is a small, opinionated tool — the contribution surface is deliberately narrow so we can keep it fast, secure, and predictable.

## Quick start

```bash
git clone https://github.com/agenticailab01/lensify
cd lensify
python3 -m pytest tests/ -q                  # 527 tests
python3 -m pytest tests/benchmark_perf.py -q # 17 perf + security budgets
python3 skills/lensify/scripts/scan.py . --no-git
```

Everything should be green before you start editing.

## What contributions we welcome

| Category | Examples |
|---|---|
| **New framework adapters** | Next.js, Astro, NestJS, Django, Spring Boot — see `skills/lensify/references/adapter-sdk.md` |
| **Bug fixes** | Anything correctness or perf-related in shipped adapters or hooks |
| **Documentation** | README clarifications, integration recipes, FAQ additions |
| **Performance work** | Anything that keeps the perf budgets green while doing more |
| **Test improvements** | Better fixtures, edge-case coverage |

## What contributions we won't accept

See `GOVERNANCE.md` for the full list. The non-negotiables:

- No `exec` / `eval` / `pickle.loads` / `shell=True` / `os.system` in shipped code (CI-enforced)
- No outbound HTTP outside `llm_client.py` and `api.anthropic.com` (CI-enforced)
- No telemetry sent off-device
- No adapters that ship hardcoded credentials
- No "give the agent shell access" features

## Workflow

1. **Open an issue first** for anything bigger than a typo fix. We may already be working on it, or there may be context that affects your approach.
2. **Fork + branch** off `main`. Name your branch descriptively (`adapter/nextjs`, `fix/sqlalchemy-redaction`).
3. **Stay small** — one logical change per PR. 200-line PRs are easier to review than 2,000-line ones.
4. **Tests with your change** — every new adapter has tests, every bug fix gets a regression test.
5. **Run the perf harness** before pushing — `python3 -m pytest tests/benchmark_perf.py -q`. All 17 must pass.

## Adapter contributions in detail

The fastest way to contribute is a new framework adapter. The SDK is documented at `skills/lensify/references/adapter-sdk.md` with a template at `skills/lensify/scripts/frameworks/_template/`.

A complete adapter PR looks like:

```
skills/lensify/scripts/frameworks/_yourpack/yourframework.py  (~80-120 LOC)
skills/lensify/scripts/frameworks/manifest.json               (1 entry added)
tests/test_yourpack_adapters.py                                   (~5-10 tests)
CHANGELOG.md                                                       (new entry)
```

Adapters must follow the R1–R5 rules listed in the SDK doc. R1 and R3 are CI-enforced.

## Style

- **Python 3.9+ compatible** — we use `from __future__ import annotations` everywhere
- **Pure stdlib** — adding a third-party runtime dep needs a strong justification + maintainer approval
- **Docstrings on every public symbol** — explain *why*, not *what*
- **No emojis in code or output** (except where users explicitly request emoji-rich output)
- **Type hints** where they help — we're not religious about full coverage

## CI

GitHub Actions runs on every PR:

- `pytest tests/` — full suite (527 tests today)
- `pytest tests/benchmark_perf.py` — 17 perf + security budgets
- Static analysis: no `exec`/`eval`/`pickle`/`shell=True` in shipped code
- Hook-isolation check: hook scripts never import `frameworks/*`

All four must be green before merge.

## Releases

We use semver. The current major series is `0.x` while we shape the public API. Plan:

- `0.15.x` — current; layered distribution shipping (plugin + MCP + CLI + AGENTS.md)
- `0.16.x` — multi-modal lightweight (SQL, shell, Dockerfile, Markdown docs)
- `1.0.0` — API stabilization milestone

## Questions

- Open an issue on GitHub for anything specific
- For security reports, see `SECURITY.md` (private channel)

## License

MIT. By contributing, you agree your contributions are licensed under MIT.
