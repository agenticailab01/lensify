# Lifetime Telemetry (Phase 8)

The statusline badge and `/lensify stats` command surface the cumulative
value of every prior phase. Until v0.6.0 the savings were real but invisible
to the user — this phase makes them visible, which is the difference between
"interesting plugin" and "must-install plugin."

## What's tracked

| Counter | Bumped by | Estimated savings (per event) |
|---|---|---|
| `dedup_count` | dedup_hook | ~350 tokens (avg file Read replaced) |
| `compressions` | compress_hook | exact bytes_saved / 3.5 ≈ tokens |
| `compactor_runs` | compact.py | meta["tokens_reclaimed_est"] |
| `memory_recalls` | memory_loader.py | not directly measurable |
| `memory_saves` | compact.py | not directly measurable |
| `selective_injections` | inject_hook | ~850 tokens (full capsule vs slice delta) |
| `scan_count` | scan.py | (no per-event token estimate) |

Plus `tokens_saved` (sum of all events) and `compress_bytes_saved` (raw byte
total for the compression "MB processed" stat).

## Storage

```
~/.lensify/stats.json
```

Override via `LENSIFY_STATS_HOME` (used by tests + power users who want a
project-local stats file). On read failure or parse failure, the module
returns fresh-init stats — telemetry must never block agent operations.

The file is atomically updated via temp + rename, so concurrent hook calls
won't corrupt it.

## Statusline format

Examples by event volume:

```
[LENS] ⛏ 47.2k tok                 (low — just dedup so far)
[LENS] ⛏ 152.3k · 87d · 5c          (moderate — 87 dedups, 5 compactor runs)
[LENS] ⛏ 1.4M · 1.2k d · 23c        (heavy use over months)
```

The statusline is intentionally cryptic-but-compact to fit Claude Code's
narrow status bar. Mouseover/expansion is the user's job via
`/lensify stats`.

## `/lensify stats` — full report

```
Lensify — lifetime stats
========================================
Tracking since:   2026-05-10 (13 day(s) ago)
Tokens saved:     152,340
Estimated $ saved: ~$2.29  (at Opus input pricing)

By event type:
  Dedup hooks          87 events  (~30,450 tok)
  Compressions         23 events  (~24,200 tok, 487.2KB raw)
  Compactor runs        5 runs
  Memory recalls        3 events
  Memory saves          5 events
  Selective inject    142 prompts
  Scans                 8 runs

Top projects by tokens saved:
  /Users/dev/work/customer-portal              98,200 tok
  /Users/sachin/work/internal-api             54,140 tok
```

## USD estimate

Default is Claude Opus input pricing ($15 / M tokens). Override via
`LENSIFY_USD_PER_MTOK` for a different model:

```bash
export LENSIFY_USD_PER_MTOK=0.80   # Haiku rate
lensify stats                       # numbers now reflect Haiku pricing
```

This is a rough estimate — assumes every token saved was an input token.
Output savings (from caveman-style compression) aren't counted here; that's
the complementary plugin.

## Privacy

- Counters are integers and project paths. **No prompt text, no file contents,
  no telemetry is sent anywhere.**
- Stats live in `~/.lensify/stats.json`. Wipe at any time with
  `--reset` or `rm ~/.lensify/stats.json`.
- Per-project paths are stored to enable the "Top projects" table; remove
  them by editing the JSON if desired.

## Opt out

```bash
export LENSIFY_STATS=0   # disable lifetime tracking
```

All hooks tolerate the stats module being unavailable — telemetry is purely
additive; nothing in the agent path depends on it.

## What's NOT done

- Per-day / per-week breakdown
- Lifetime cost graph
- Export to CSV / Prometheus
- Multi-user / team aggregation (per-user only)

If users want richer dashboards they can pipe `--json` output into their
own tooling. The plugin deliberately stops at "make the savings visible";
analytics is downstream.
