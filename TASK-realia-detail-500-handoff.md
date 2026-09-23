<!-- markdownlint-disable MD013 MD041 -->

# TASK-realia-detail-500 Handoff — PR #767 "Load Realia entries whose optional fields are stored as null"

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 |
| **Pull request** | [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767) `fix-realia-detail-unloadable-entries` → `master` |
| **Fix commit** | `19dad310` (pushed) |
| **State** | Open, `REVIEW_REQUIRED`, mergeable |
| **Origin** | Finding R4 in the PR #735 review (`TASK-pr735-review.md` on that branch) |
| **Work notes in this branch** | `TASK-realia-detail-500-*`, `TASK-realia-fix-push-*`, `TASK-realia-fix-pr-*` and this file. They are committed on purpose for handoff. **Delete them before merge.** |

## In simple words

Some old Realia records store an optional field as `null`, for example `type: null`. Opening such a page returned an error (500). Now `null` is read as "empty", so the page opens.

## What was done

- `RealiaEntrySchema` gets a `@pre_load` hook, `treat_null_as_absent`, that drops top-level `null` values before loading, so they take their normal defaults. `_id: null` and wrong-shaped values (like `relatedTerms: [5]`) are still rejected.
- Also fixed 2 pyright errors that were already in the same file on `master`: `ReallexikonReferenceField` used `attr_name` where marshmallow's `Field` uses `attr`.
- Added `ebl/tests/realia/test_realia_null_fields.py`, 21 tests. 18 of them fail without the fix.
- Local gates all pass, including the full suite (4853 passed) and 100% coverage on the changed files. On the running app, `type: null` and `realiaId: null` return 200 (500 on `master`).

## Open items

| # | What | Status |
| --- | --- | --- |
| 1 | **Sourcery comment** (`realia_schemas.py:132`): the hook checks `isinstance(data, dict)`, so a non-`dict` `Mapping` would skip the null handling. Mongo returns plain dicts here today, so nothing breaks now, but checking `Mapping` is more correct. | **Open.** Small fix plus a test; waiting for a decision |
| 2 | **CI flake**: in one of the two CI runs, `test_app_bootstrap.py::test_create_context_bootstraps_cache_indexes` failed on PyPy 3.11 with `PermissionError` on the in-memory `mongod` binary (Python 3.11 in that run was cancelled). The other run passed everything, and the test doesn't touch Realia. | **Open.** Re-run the failed job to clear the red mark |
| 3 | Records with wrong-shaped values (for example `relatedTerms: [5]`) still return 500. | Out of scope, needs a data cleanup |

## Next steps

1. Decide on the Sourcery comment (item 1). If fixing: switch `dict` to `Mapping`, add a test, run all gates, then commit and push (each needs approval).
2. Re-run the failed CI job (item 2).
3. Get a human review, then delete the `TASK-*.md` files in a last commit before merging.
4. Once #735 is merged too, `/realia/all` starts listing the records this fix makes loadable. No extra change is needed.
