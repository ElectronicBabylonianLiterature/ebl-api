# TASK realia-fix-pr — Log

## 2026-09-23

- Created TODO and log first. Request: "Open the new PR".
- Remote head `19dad310` = local; no existing PR for the branch.
- Wrote the body in the scratchpad (unwrapped, no attribution lines).
- `gh pr create --base master --head fix-realia-detail-unloadable-entries`
  → #767. Read back: OPEN, `master` ← branch, head `19dad310`, 2 files
  (+63/−3), body length equals the file (1910).
- Linked #767 from R4 in `TASK-pr735-review.md` and in the handoff.
- CI on #767 (two runs of the same commit `19dad310`):
  - Run A: `Test Python pypy-3.11` failed, 1 test:
    `test_app_bootstrap.py::test_create_context_bootstraps_cache_indexes`,
    `PermissionError` executing the pymongo_inmemory `mongod` binary
    (4852 passed). Its `Test Python 3.11` was cancelled (fail-fast).
  - Run B: pypy-3.11 passed, 3.12 passed, 3.11 still running.
  - Same commit passes pypy in run B, the test doesn't touch Realia, and
    none of the last 15 failed runs in the repo show this error: a one-off
    runner flake. Not re-run (needs the user's go-ahead).
  - CodeQL, GitGuardian, Sourcery, qlty (no blocking issues, coverage diff
    100%) pass.
- Sourcery review on #767, 1 finding (`realia_schemas.py:132`): the hook
  checks `isinstance(data, dict)`, so a non-dict `Mapping` would skip the
  null handling. The repo configures no custom Mongo `document_class`, so
  real documents are plain dicts today, but checking `Mapping` is more
  correct and costs nothing. Fix needs a code change, commit and push:
  asking the user.
- CI finished. Run B fully green (3.11, 3.12, pypy-3.11). Run A: pypy-3.11
  failed (the flake above), 3.11 cancelled. Everything else passes;
  `docker` skipped.
