# TASK-realia-all — TODO (fix reallexikon reference null-check)

- [x] Diagnose why the committed stub-exclusion excluded nothing on live data.
- [x] Fix `_reallexikon_reference_count` to match the domain rule (dict needs a
      non-empty `id`; string must be non-empty).
- [x] Verify against the live 24k dataset: 0 disagreements vs the domain rule.
- [x] Extend repo test with dict-without-id / empty-string / string reference.
- [ ] Gates: `task format`, `task test`, 100% coverage on changed files,
      `flake8 --max-line-length=120`, `mypy`, `task lint-md`.

> Remove this file (and `TASK-realia-all-log.md`) before the PR is merged.
