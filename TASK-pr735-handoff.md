<!-- markdownlint-disable MD013 MD041 -->

# TASK-pr735 Handoff — PR #735 and the Realia detail-route follow-up

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 |
| **PR #735** | [#735](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735) `add-realia-slugs-endpoint` → `master`, head `a93ae870` (pushed), CI all green |
| **Follow-up** | Branch `fix-realia-detail-unloadable-entries` (from `master` @ `cd46110c`), opened as [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767) (`19dad310`), `REVIEW_REQUIRED`; its own handoff is `TASK-realia-detail-500-handoff.md` on that branch |
| **Review verdict (#735)** | **Approve**; merge waits only on Fabdulla1's re-review |
| **Work notes in this branch** | `TASK-pr735-review.md` (the review), `TASK-pr735-address-log.md` (drafted replies), this file, and the other `TASK-pr735-*` / `TASK-handoff-update-*` / `TASK-docs-commit-*` TODOs and logs. Committed on purpose for handoff. **Delete them before merge.** |

## In simple words

- **#735** adds `/realia/all`, the list of Realia pages that the frontend sitemap needs. The code is good: every listed page opens, a broken record can't crash the list, and in production (Redis) the list is computed at most once every 10 minutes.
- The only real problem in the last review was that work notes (`TASK-*.md` files) had been committed into the PR. That's fixed and pushed (`a93ae870`).
- Fabdulla1 still has "changes requested" on #735. Their points are all fixed, but nobody has replied yet, so the PR can't merge.
- Separately, some old Realia records have a field stored as `null`, and opening their page gave an error (500). The follow-up branch fixes that: `null` is now read as "empty".

## What was done (2026-09-23)

1. **Re-review of #735 at `6394de8d`.** Fetched every review and comment (Sourcery, Fabdulla1), checked CI, qlty and CodeQL, ran all local gates and ran the real service against a throwaway database (null, `simple` and Redis cache). Found 8 `TASK-*.md` files inside the PR. No dev container or config changes.
2. **Removed the TASK files from #735.** Commit `a93ae870` (8 deletions only), pushed once. The PR is now 14 files, CI green.
3. **Checked production caching.** `ElectronicBabylonianLiterature/infrastructure` `ebl.yml` sets `CACHE_CONFIG` to Redis. Tested with a local Redis and two app processes: 6 requests made 1 database query.
4. **Rewrote the review** (`TASK-pr735-review.md`): header with verdict, short summary first, findings R1–R5 with details.
5. **Follow-up fix (R4).** `RealiaEntrySchema` now drops top-level `null` values before loading, so they get their normal defaults. The same file also had 2 pyright errors that were already on master: `ReallexikonReferenceField` named a parameter `attr_name` where the base class uses `attr`. Fixed. Added `ebl/tests/realia/test_realia_null_fields.py` (21 tests). Committed as `19dad310` and pushed. All gates pass (full suite 4853 passed), and the running service returns 200 for `type: null` and `realiaId: null`.

## Findings and their status

| ID | Where | Severity | What | Status |
| --- | --- | --- | --- | --- |
| R1 | #735 | High | 8 `TASK-*.md` work-note files committed into the PR | **Fixed** (`a93ae870`, pushed) |
| R2 | #735 | Medium | Fabdulla1's review (2026-08-18) and 2 inline threads have no reply; review still `CHANGES_REQUESTED` | **Open**, replies drafted in `TASK-pr735-address-log.md`; you chose not to post them yet |
| R3 | #735 | Info | Caching only helps if a cache backend is set | **Resolved**, production uses Redis |
| R4 | `master` | Info | `/realia/{id}` returns 500 for records stored with `null` fields | **Fixed in [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767)**, open. Sourcery comment (`dict` → `Mapping`) and one CI flake still to handle there |
| R5 | `master` | Info | mypy errors (26) and uncovered lines in untouched, imported code | No action, pre-existing |

Still out of scope: records with wrong-shaped values (for example `relatedTerms: [5]`) still return 500 on their page. They are left out of `/realia/all`, so the sitemap never links to them. Fixing them means cleaning the data.

## Next steps

1. **Follow-up PR [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767):** decide on Sourcery's `Mapping` comment, re-run the flaky CI job, then get it reviewed and merged. See `TASK-realia-detail-500-handoff.md` on that branch.
2. **Dependabot alert 75** (high) on `master`, reported by GitHub on push. This token can't read it (403); check it in the GitHub UI.
3. **#735, R2:** when you're ready, post the drafted replies, resolve the two threads and request a re-review from Fabdulla1.
4. **After #735 merges:** `/realia/all` automatically starts listing the records the follow-up fix makes loadable. No extra change is needed.
5. **Before any merge:** delete all `TASK-*.md` work notes in a last commit. They are committed on purpose for handoff but must not reach `master`.

## Notes for whoever picks this up

- **Work notes are committed on purpose here** (for handoff). Before merging, remove them in one commit. Otherwise stage files by name, never with `git add -A`: `TASK-*.md` files reached #735 by accident four times.
- **pyright:** `task type-pyright` only checks committed changes. On a dirty tree, run `npx pyright@1.1.411 <files>` directly.
- **Stopping local servers:** `pgrep -f <pattern> | xargs kill` can match its own shell when the same command line contains the pattern. Find the pid in one call and kill it in another.
- **Never use `.env`** for local runs: it points at the production database. Use `127.0.0.1:27017` and a throwaway database.
