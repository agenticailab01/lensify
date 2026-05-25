## What this PR does

One-paragraph summary.

## Linked issue

Closes #

## Type of change

- [ ] Bug fix
- [ ] New framework adapter
- [ ] Doc / DX improvement
- [ ] Performance
- [ ] Other (describe)

## Test status

- [ ] `python3 -m pytest tests/ -q` passes
- [ ] `python3 -m pytest tests/benchmark_perf.py -q` passes (all 17 budgets)
- [ ] New tests cover the change (regression test for bugs, full coverage for adapters)
- [ ] If adapter PR: validated `validate_class()` is clean, R1–R5 rules respected

## Checklist

- [ ] CHANGELOG.md updated under "Unreleased" or a new version section
- [ ] No new third-party runtime dependencies (or if there are, justified in the PR description)
- [ ] No `exec`/`eval`/`pickle`/`shell=True`/`os.system` in shipped code
- [ ] No outbound HTTP except through `llm_client.py`
- [ ] Documentation updated if the feature is user-visible

## Notes for the reviewer

Anything specific you want them to look at, alternative approaches you considered, etc.
