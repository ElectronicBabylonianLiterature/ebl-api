<!-- markdownlint-disable MD013 MD041 -->

# TASK-realia-detail-500 Handoff — PR #767 "Load Realia entries whose optional fields are stored as null"

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 |
| **Pull request** | [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767) `fix-realia-detail-unloadable-entries` → `master` |
| **Fix commit** | `19dad310` (pushed) |
| **State** | Open, `REVIEW_REQUIRED`, mergeable |
| **Origin** | Finding R4 in the PR #735 review (`TASK-pr735-review.md` on that branch) |
| **Work notes in this branch** | `TASK-realia-detail-500-*`, `TASK-realia-fix-push-*`, `TASK-realia-fix-pr-*`, `TASK-realia-mapping-*` and this file. They are committed on purpose for handoff. **Delete them before merge.** |

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
| 1 | **Sourcery comment** (`realia_schemas.py:132`): the hook checks `isinstance(data, dict)`, so a non-`dict` `Mapping` would skip the null handling. Mongo returns plain dicts here today, so nothing breaks now, but checking `Mapping` is more correct. | **Fixed locally, not committed:** the hook now checks `typing.Mapping`, and `test_null_field_in_non_dict_mapping_loads_as_absent` covers it (fails without the change). All gates pass (4854 passed) |
| 2 | **CI flake**: in one of the two CI runs, `test_app_bootstrap.py::test_create_context_bootstraps_cache_indexes` failed on PyPy 3.11 with `PermissionError` on the in-memory `mongod` binary (Python 3.11 in that run was cancelled). The other run passed everything, and the test doesn't touch Realia. | **Resolved:** CI on the next head (`3ac43099`) passed all 15 checks, no re-run needed |
| 3 | Records with wrong-shaped values (for example `relatedTerms: [5]`) still return 500. | Out of scope, needs a data cleanup |

## Next steps

1. Commit and push the `Mapping` fix (item 1); each needs approval. Then reply to Sourcery's comment.
2. Get a human review, then delete the `TASK-*.md` files in a last commit before merging.
3. Once #735 is merged too, `/realia/all` starts listing the records this fix makes loadable. No extra change is needed.
