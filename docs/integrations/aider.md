# Aider

Aider has no plugin system but reads context from `CONVENTIONS.md`, `AGENTS.md`, and similar files. Lensify integrates via the **CLI + AGENTS.md** channels.

## Install

```bash
pip install lensify   # once published to PyPI
# OR
git clone https://github.com/agenticailab01/lensify ~/lensify
alias lensify="python3 ~/lensify/skills/lensify/scripts/scan.py"
```

## Use the AGENTS.md write mode

This is the cleanest integration. Run once per project:

```bash
lensify . --install-agents-md
```

That generates the capsule and writes it into `AGENTS.md` at the project root, wrapped in idempotent `<!-- lensify-begin -->` / `<!-- lensify-end -->` markers.

Configure Aider to read it (`.aider.conf.yml`):

```yaml
read:
  - AGENTS.md
```

Now every Aider session starts with the capsule in context — orientation tokens drop 70-90%.

## Refresh on demand

```bash
lensify . --install-agents-md
```

The markers make this idempotent — only the capsule block is replaced; any other content you've added to `AGENTS.md` is preserved.

## Or use the raw capsule

If you'd rather keep `AGENTS.md` manually authored, drop the capsule somewhere Aider reads it:

```bash
lensify . --capsule-only
cp lensify-out/LENS.capsule.md CONVENTIONS.md
```

```yaml
# .aider.conf.yml
read:
  - CONVENTIONS.md
```

## Compactor + Aider

When a session gets long:

```bash
lensify . --output lensify-out
# Then in a separate terminal, generate the compactor output:
python3 ~/lensify/skills/lensify/scripts/compact.py .
# Open lensify-out/WORKING_CONTEXT.md, paste at the top of your next Aider session
```

The compactor benefits depend on Aider exposing the session state we track — without hook support, it works best when you also use the CLI to record what you've done.
