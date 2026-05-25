# Aider

Aider has no plugin system but reads context from `CONVENTIONS.md`, `AGENTS.md`, and similar files. ProjectLens integrates via the **CLI + AGENTS.md** channels.

## Install

```bash
pip install projectlens   # once published to PyPI
# OR
git clone https://github.com/agenticailab01/projectlens ~/projectlens
alias projectlens="python3 ~/projectlens/skills/projectlens/scripts/scan.py"
```

## Use the AGENTS.md write mode

This is the cleanest integration. Run once per project:

```bash
projectlens . --install-agents-md
```

That generates the capsule and writes it into `AGENTS.md` at the project root, wrapped in idempotent `<!-- projectlens-begin -->` / `<!-- projectlens-end -->` markers.

Configure Aider to read it (`.aider.conf.yml`):

```yaml
read:
  - AGENTS.md
```

Now every Aider session starts with the capsule in context — orientation tokens drop 70-90%.

## Refresh on demand

```bash
projectlens . --install-agents-md
```

The markers make this idempotent — only the capsule block is replaced; any other content you've added to `AGENTS.md` is preserved.

## Or use the raw capsule

If you'd rather keep `AGENTS.md` manually authored, drop the capsule somewhere Aider reads it:

```bash
projectlens . --capsule-only
cp projectlens-out/LENS.capsule.md CONVENTIONS.md
```

```yaml
# .aider.conf.yml
read:
  - CONVENTIONS.md
```

## Compactor + Aider

When a session gets long:

```bash
projectlens . --output projectlens-out
# Then in a separate terminal, generate the compactor output:
python3 ~/projectlens/skills/projectlens/scripts/compact.py .
# Open projectlens-out/WORKING_CONTEXT.md, paste at the top of your next Aider session
```

The compactor benefits depend on Aider exposing the session state we track — without hook support, it works best when you also use the CLI to record what you've done.
