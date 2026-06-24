# TASK-715-typecheck — TODO

Fix failing CI (PR #715 `Add Realia module`, branch `add-realia`).

- [x] Identify failing CI step (pyre **Type Check**, 2 errors)
- [x] Fix `test_realia_entry.py:83` — Optional narrowing for `reallexikon.id`
- [x] Fix `test_realia_repository.py:118` — Optional narrowing for `reallexikon.reference`
- [x] `poetry run pyre check` — no type errors
- [x] Pre-commit hard gates:
  - [x] `task format` — 681 files already formatted
  - [x] `task test` — 3582 passed, 2 skipped, 1 xfailed
  - [x] coverage on changed files — both are test files; all tests execute
  - [x] `poetry run flake8 <changed> --max-line-length=120` — 0 errors
  - [x] `poetry run mypy <changed> --ignore-missing-imports` — 0 errors
- [x] Fix mypy errors in `scopes.py` (rename bare `prefix`/`suffix` locals that
      mypy mis-detected as Final enum members)
- [x] Add `ebl/tests/common/test_scopes.py` → `scopes.py` at 100% coverage
- [x] `ruff check` (qlty lint) on all changed files — All checks passed
- [x] Final `task test` — 3588 passed, 2 skipped, 1 xfailed; `pyre check` clean
- [ ] Reminder: remove TASK-715-typecheck-*.md before merge
