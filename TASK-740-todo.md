# TASK-740 TODO — 4 unit tests failing on remote CI

Task: CI reports 4 failing unit tests while the local suite passes. Find out
how that happened, and fix it.

## Investigate

- [x] Fetch the failing CI run and identify the 4 tests
- [x] Read the actual failure output (not just the names)
- [x] Reproduce locally — 2-file repro fails in 2.5s
- [x] Establish the root cause: unstubbed module-level mockito stub on
      `pymongo.MongoClient` in `test_context_fallback_to_mongo`
- [x] Confirm pre-existing, not this branch: identical failure on pristine
      `origin/master`; this branch touches neither file
- [x] Attribute: `450adab53`, Wentao Che, 2025-11-08, PR #636

## Fix

- [x] Take the `when` fixture in `test_context_fallback_to_mongo`
- [x] Harden 17 other tests with the same leak pattern (5 files)
- [x] Drop the now-unused module-level `mockito.when` imports
- [x] Confirm on the merged tree CI builds — full suite 3928 passed
- [x] Committed as `8e70bfff`

## Phase 2 — pyright gate exposed by the commit

Committing the test files pulled them into `task type-pyright`
(`origin/master...HEAD`, committed files only), surfacing **21 pre-existing
pyright errors**. Verified identical on pristine `origin/master`, so none
were introduced here — they were simply never checked.

User decision: **fix all 21**, keeping every preventive fix.

- [x] Confirm all 21 are pre-existing on master
- [x] Ask the user rather than unilaterally narrowing scope
- [x] `test_cropped_annotations_service.py` — 13 errors: cast `mock()` to
      `AnnotationsRepository` / `CroppedSignImagesRepository` /
      `FragmentRepository` at the assignment
- [x] `test_migrate_cropped_images.py` — 5 errors: cast to `Context`; build
      attributes via `mock({...})` instead of assigning onto `Dummy`
- [x] `test_retrieve_annotations.py` — 2 errors: `mock({...})` config
- [x] `test_update_ocred_signs.py` — 1 error (**genuine test bug**): passed a
      `list[str]` where `number_str: str` was expected
- [x] Re-run pyright: 0 errors

## Gates (all — nothing skipped)

- [x] `task format` — 747 files already formatted
- [x] `task lint` (ruff) — all checks passed
- [x] `task type` (pyre — the checker CI enforces) — No type errors found
- [x] `task type-pyright` — 0 errors (was 21)
- [x] `task test` — 3923 passed, 0 failures
- [x] Coverage — no source modules changed; `.coveragerc` omits `ebl/tests/*`
- [x] `poetry run flake8 <changed> --max-line-length=120` — clean
- [x] `poetry run mypy <changed> --ignore-missing-imports` — clean
- [x] `task lint-md` — 0 errors
- [x] No service run needed — test-only change, no runtime surface
- [x] `task test-all` aggregate — exit 0

## Reminders

- `TASK-740-todo.md` and `TASK-740-log.md` must be removed before merge —
  **but not yet**: work is still in progress and they stay updated until it
  is done.
- Nothing is to be committed unless explicitly requested.
- Do not rewrite pushed history. `8e70bfff` is committed but not yet pushed;
  `f0026098` and earlier are on the remote.
