"""Adapter SDK template — copy this directory to start a new pack.

The files here are a *self-contained working example* of a framework adapter
plus its test file. Steps to create your own:

    1. Copy `_template/` to `_<your_pack>/`
    2. Rename `template.py` → `<your_framework>.py`
    3. Replace TemplateAdapter with YourFrameworkAdapter
    4. Update detect_signatures + regex patterns
    5. Add an entry to ../manifest.json
    6. Copy `test_template_adapter.py` → tests/test_<your_pack>_adapters.py
    7. Run `python3 -m pytest tests/ -q` — must stay green
    8. Run `python3 -m pytest tests/benchmark_perf.py -q` — must stay green

See `references/adapter-sdk.md` for the full contract + rules.
"""
