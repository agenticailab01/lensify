# Read Dedup Hook

Lensify ships a `PreToolUse` hook that intercepts every `Read` tool call
and tells the agent when it's about to re-read a file it has already opened
in this session.

## Why this saves tokens

In a long Claude session, the agent often re-reads the same file 3–5 times:
once for orientation, again for a different question, again when reasoning,
again when writing a fix. Each read consumes 200–500 tokens of context that
is already there from the earlier read.

The hook turns each duplicate read attempt into a one-line "you've seen this"
note. The agent then chooses to use what it already has rather than spending
another 300–500 tokens re-reading.

## How it works

1. **`SessionStart`** hook fires when Claude opens a new session — clears
   `.lensify-session.json` and starts a fresh tracker.
2. **`PreToolUse`** hook fires before every `Read` tool call:
   - Resolves the file path to absolute form
   - Computes a short SHA-256 of the file contents
   - Looks up the file in the session tracker
   - If unseen: records it and lets the read proceed silently
   - If seen with **same hash**: surfaces a "you already read this; consider
     skipping" note via `additionalContext`
   - If seen with **different hash**: surfaces a "file changed since you last
     read it" note (re-read is legitimate)
3. State persists in `.lensify-session.json` in the project root.

## State file format

```json
{
  "version": 1,
  "session_id": "abc-123",
  "project_root": "/abs/path/to/project",
  "started_at": 1716544800.123,
  "current_turn": 5,
  "reads": {
    "/abs/path/to/file.py": {
      "rel_path": "src/file.py",
      "abs_path": "/abs/path/to/file.py",
      "content_hash": "ab12cd34ef56...",
      "first_turn": 2,
      "last_turn": 5,
      "read_count": 3,
      "size_bytes": 4216,
      "first_seen_at": 1716544830.456
    }
  }
}
```

## What the agent sees

When the agent attempts a duplicate read, the hook adds context like:

> DEDUP: `app/domain/auth.py` was already read in this session at turn 2.
> The file's contents have NOT changed (sha256 unchanged). If you already
> have the information you need from the earlier read, consider skipping
> this read and proceeding.

The note is advisory — the read is not blocked. The agent decides.

## Limits

- **Hard cap**: 500 tracked files per session. Older entries drop first.
- **Hash window**: short SHA-256 prefix (32 chars). Collision risk is
  negligible for file-content comparison.
- **Turn tracking** is coarse — the hook bumps the turn counter on the first
  Read after loading state; multiple reads inside one turn don't all bump.
  This is fine for the dedup note (which only needs a "you saw this earlier"
  signal, not exact turn numbers).

## Opt out

```bash
export LENSIFY_DEDUP=0   # disables both hooks
```

## Inspect session state

```bash
python /path/to/lensify/skills/lensify/scripts/dedup_hook.py --stats /path/to/project
```

Output:

```json
{
  "files_tracked": 12,
  "total_read_attempts": 18,
  "duplicates_alerted": 6,
  "session_id": "abc-123",
  "current_turn": 7
}
```

`duplicates_alerted` is the count of reads where the hook surfaced a "you
already saw this" note — the direct save signal.

## What the hook does NOT do

- It does not block reads (too aggressive — the agent might genuinely need
  the file content).
- It does not modify the Read response or strip output.
- It does not work across sessions — state resets at every SessionStart.
- It does not work on tools other than `Read` (Bash, Edit, Write all
  proceed unaffected).

## Platforms

Hooks are a Claude Code feature. On platforms without hook support (Cursor,
OpenCode in basic mode, etc.), the dedup feature is silently inactive. The
core lens + capsule features still work on every platform.
