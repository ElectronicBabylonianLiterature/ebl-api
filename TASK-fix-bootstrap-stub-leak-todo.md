# TASK: Fix flaky test_app_bootstrap failures (mockito stub leak)

## Problem

CI (pypy-3.11) intermittently fails 4 tests in `ebl/tests/test_app_bootstrap.py`
with `mockito.invocation.InvocationError` from `pymongo_inmemory/mongod.py:114`
(`pymongo.MongoClient('mongodb://localhost:27017')` rejected; only
`mongodb://test:27017` stubbed).

## Root cause

`test_context_fallback_to_mongo` in
`ebl/tests/fragmentarium/test_retrieve_annotations.py` stubs
`pymongo.MongoClient` via the module-level `mockito.when` and never unstubs.
The pytest-mockito plugin only auto-unstubs when a test uses one of its
fixtures (`when`, `unstub`, ...). This test takes only `monkeypatch`, so the
strict stub leaks to later tests in the same xdist worker.

## TODO

- [x] Reproduce leak deterministically (leaker + bootstrap test, no xdist)
- [x] Confirm plugin auto-unstub semantics (plugin.py hook)
- [x] Fix `test_context_fallback_to_mongo` to use the `when` fixture
- [x] Fix `test_argument_parsing_defaults` (same module-level `when` leak)
- [x] Remove now-unused module-level `when` import
- [x] Verify: reproduction sequence now passes (5 passed)
- [x] Verify: full `test_retrieve_annotations.py` + `test_app_bootstrap.py` pass
- [x] Gates: flake8, black, mypy(changed file), pyre (task type) — all clean
- [x] Fix Pylance/pyright reportAttributeAccessIssue (dict-config mock)
- [x] Full `task test` suite: 3848 passed, 0 failures
- [x] Gates: task format, task lint-md — clean
- [x] Commit (docs included, per user request)
