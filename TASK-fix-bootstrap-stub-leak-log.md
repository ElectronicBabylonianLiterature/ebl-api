# WORK LOG: Fix flaky test_app_bootstrap failures

## Investigation

- PR #741 CI: `Test Python pypy-3.11` failed, 4 tests in
  `ebl/tests/test_app_bootstrap.py`; same commit passed on a full re-run.
- PR #741 diff touches only afo_register repo/tests + .gitignore + TASK docs —
  not test_app_bootstrap. Failure is unrelated to the PR's logic.
- Error: `mockito.invocation.InvocationError` at
  `pymongo_inmemory/mongod.py:114`, `pymongo.MongoClient(...)` call.
- Grep found `when(pymongo).MongoClient("mongodb://test:27017")` in
  `test_retrieve_annotations.py::test_context_fallback_to_mongo` (module-level
  `when`, no fixture, no unstub).
- Read `pytest_mockito/plugin.py`: global `unstub()` runs after a test only if
  it uses a plugin fixture (when/unstub/when2/expect/patch/spy2).
- Reproduced deterministically on CPython:
  `pytest -p no:xdist <leaker> test_app_bootstrap::test_get_app_bootstraps`
  -> exact CI error. Confirmed root cause.

## Changes

`ebl/tests/fragmentarium/test_retrieve_annotations.py`:

- `test_context_fallback_to_mongo(monkeypatch)` ->
  `test_context_fallback_to_mongo(monkeypatch, when)` so the pytest-mockito
  plugin auto-unstubs `pymongo.MongoClient` at teardown (fixes the leak).
- `test_argument_parsing_defaults()` -> `test_argument_parsing_defaults(when)`
  (same latent module-level `when` leak onto the `retrieve_annotations` module).
- Removed now-unused module-level `when` import (all tests use the fixture).
- (Pre-existing on-disk change, kept: four inline comments removed — aligns
  with the project's "no comments" guideline.)
- Fixed 2 Pylance/pyright `reportAttributeAccessIssue` errors in
  `test_argument_parsing_defaults`: build the context mock via the dict-config
  idiom `mock({"annotations_repository": mock(), "photo_repository": mock()})`
  instead of assigning attributes to a bare `Dummy` (mockito stores non-function
  dict values as plain attributes, so runtime behavior is unchanged).

## Verification

- Repro sequence (leaker + all test_app_bootstrap tests, no xdist): 5 passed
  (previously the first bootstrap test failed with InvocationError).
- Full `test_retrieve_annotations.py`: 7 passed (with stricter
  `verifyStubbedInvocationsAreUsed` now active on the two fixture-using tests).
- flake8 (max-line-length=120): 0 errors. black --check: clean.
- mypy on changed file: clean (89 errors reported are pre-existing in other
  source files, not the test; CI enforces pyre, not mypy).
- pyre (`task type`, the CI gate): No type errors found.

## Pre-commit gates (all pass)

- `task format`: 749 files formatted, no changes.
- `task test`: 3848 passed, 2 skipped, 1 xfailed, 0 failures.
- coverage: only `ebl/tests/*` changed (omitted by `.coveragerc`); both changed
  tests execute — no production line uncovered.
- `flake8 --max-line-length=120`: 0 errors.
- `pyre` (`task type`): no type errors. `pyright`: 0 errors.
- `task lint-md`: 0 errors.

## Remaining

- Push to remote PR branch so CI re-runs green (awaiting user).
- Task docs committed per user request; remind to remove before merge.
