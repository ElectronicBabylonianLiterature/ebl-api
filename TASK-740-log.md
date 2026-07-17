# TASK-740 Work Log — 4 unit tests failing on remote CI

Date: 2026-07-16. Branch: `add-realia-annotation-api`.

## 1. Starting position

User reports 4 unit tests failing on remote CI while `task test-all` passes
locally with 3923 passed. The discrepancy itself is the thing to explain.

## 2. The failures

CI run 29515998161 (`pull_request`, sha `51e4be76`), job
**Test Python pypy-3.11**:

```text
FAILED ebl/tests/test_app_bootstrap.py::test_get_app_bootstraps
FAILED ebl/tests/test_app_bootstrap.py::test_create_context_helpers
FAILED ebl/tests/test_app_bootstrap.py::test_create_context_bootstraps_cache_indexes
FAILED ebl/tests/test_app_bootstrap.py::test_create_app_bootstraps_annotations_and_afo_indexes
4 failed, 3924 passed
```

All four: `mockito.invocation.InvocationError`.

```text
Called but not expected:
    MongoClient('mongodb://localhost:27017')
Stubbed invocations are:
    MongoClient('mongodb://test:27017')
```

## 3. Root cause

`ebl/tests/fragmentarium/test_retrieve_annotations.py::test_context_fallback_to_mongo`
stubbed `pymongo.MongoClient` at module level with mockito and never
unstubbed:

```python
def test_context_fallback_to_mongo(monkeypatch):   # no `when` fixture
    when(pymongo).MongoClient("mongodb://test:27017").thenReturn(mock_client)
```

The file imports `when` from mockito at module level. Every *other* test in
it takes pytest-mockito's **`when` fixture**
(`def test_create_annotations(photo_repository, when, photo)`), which unstubs
at teardown. This one did not, so its stub on the global `pymongo` module
survived the test.

`test_app_bootstrap.py` monkeypatches `ebl.app.MongoClient` to
pymongo_inmemory's client, which internally calls the real
`pymongo.MongoClient('mongodb://localhost:27017')`. That call hits the leaked
strict stub, which only allows `'mongodb://test:27017'` → `InvocationError`.

`grep -rn unstub` over the repo returns nothing: the `when` fixture is the
only cleanup mechanism, so skipping it means never cleaning up.

**Introduced by `450adab53`, Wentao Che, 2025-11-08, PR #636 "Re train ocr
model".** Not caused by this branch: this branch touches neither
`test_retrieve_annotations.py` nor `test_app_bootstrap.py`
(`git diff origin/master...HEAD` over both files is empty).

## 4. Proof it is pre-existing

Two-file repro against **pristine `origin/master`** in a throwaway worktree:

```text
pytest ebl/tests/fragmentarium/test_retrieve_annotations.py \
       ebl/tests/test_app_bootstrap.py
=> 4 failed, 7 passed in 3.98s   # identical 4 failures
```

## 5. Why it stayed hidden

`mockito.unstub()` unstubs **everything** globally. Any later test using the
`when` fixture clears the leak on teardown. So the leak only breaks a victim
when no `when`-fixture test happens to run between the leaking test and the
victim — which depends on collection order.

That is why the *same commit* `51e4be76` passed on the `push` run (all three
jobs, pypy included) and failed on the `pull_request` run: the PR run tests
master **merged in**, and master has heavily reorganised the test files
(`test_fragments_search_route.py` split into five files, plus new
`test_fragment_repository_*` files), which changes collection order.

**Limit of this investigation, stated plainly:** I could not reproduce the
exact CI combination locally. The merge tree at the pre-fix commit passes on
CPython 3.11 here (3928 passed); CI failed on **pypy-3.11**, which is not
available locally. So "merge order + pypy" is the correlated condition, and
the precise reason pypy alone trips it is not established. It does not change
the fix: the leak is removed at source, so no ordering or interpreter can
expose it.

Note: I initially assumed pytest-randomly randomised the order. It is **not
installed** — `-p no:randomly` was a no-op and ordering is deterministic. The
assumption was wrong and is corrected here.

## 6. Fix

- `test_context_fallback_to_mongo(monkeypatch, when)` — takes the `when`
  fixture, so mockito unstubs at teardown. This alone fixes the 4 failures.
- Same class of leak hardened in 17 other tests across 5 files
  (`test_retrieve_annotations`, `test_update_ocred_signs`,
  `test_migrate_cropped_images`, `test_migrate_named_entity_tags`,
  `test_cropped_annotations_service`), all of which called module-level
  `when` without the fixture.
- Module-level `from mockito import ... when` dropped from those five files
  once unused; ruff flagged it (F401/F811) and it is now gone.

**Blast radius, measured not assumed:** only the `when(pymongo)` stub breaks
`test_app_bootstrap`. Control runs on master for
`test_migrate_named_entity_tags` → `test_app_bootstrap` and
`test_update_ocred_signs` → `test_app_bootstrap` both **pass**, because those
stub their own module rather than the shared `pymongo`. The other 17 are
latent leaks of the same class, fixed preventively, not because they failed.

## 7. Verification

- Repro order now passes: 11 passed (was 4 failed).
- Reverse order: 11 passed.
- Other landmine orders: 16 and 10 passed.
- **Merge tree (master merged into this branch) + fix, full suite: 3928
  passed** — the tree CI actually builds.
- `task test-all`: exit 0 — format clean, ruff clean, pyre "No type errors
  found", pyright 0 errors, 3923 passed, lint-md 0 errors.
- flake8 clean and mypy clean on all five changed files.
- No service run: this change touches only test isolation and has no runtime
  surface.

## 8. State

Nothing committed. Throwaway worktrees removed.
