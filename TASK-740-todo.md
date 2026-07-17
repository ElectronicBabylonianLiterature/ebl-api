# TASK-740 TODO — 4 unit tests failing on remote CI

Task: CI reports 4 failing unit tests while the local suite passes. Find out
how that happened, and fix it.

## Investigate

- [ ] Fetch the failing CI run and identify the 4 tests
- [ ] Read the actual failure output (not just the names)
- [ ] Reproduce locally — determine why the local run passed
- [ ] Establish the root cause, not just the symptom
- [ ] Determine whether this branch caused it or it is pre-existing

## Fix

- [ ] Fix the root cause
- [ ] Confirm the 4 tests pass by the mechanism CI uses, not only mine

## Gates (all — nothing skipped)

- [ ] `task format`
- [ ] `task lint` (ruff)
- [ ] `task type` (pyre — the checker CI enforces)
- [ ] `task type-pyright`
- [ ] `task test` — full suite, 0 failures
- [ ] Coverage 100% on all changed modules
- [ ] `poetry run flake8 <changed> --max-line-length=120`
- [ ] `poetry run mypy <changed> --ignore-missing-imports`
- [ ] `task lint-md` if markdown changed
- [ ] Run the modified backend service if the change has a runtime surface
- [ ] `task test-all` aggregate — exit 0

## Reminders

- `TASK-740-todo.md` and `TASK-740-log.md` must be removed before merge.
- Nothing is to be committed unless explicitly requested.
- Do not rewrite pushed history (51e4be76 and earlier are on the remote).
