<!-- markdownlint-disable MD013 -->
# TASK-pr735 Review — PR #735 "Add GET /realia/all endpoint for listing Realia IDs for the sitemap"

| Field | Value |
| --- | --- |
| PR | [#735](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735) |
| Branch | `add-realia-slugs-endpoint` → `master` |
| Head reviewed | [`6394de8d`](https://github.com/ElectronicBabylonianLiterature/ebl-api/commit/6394de8d618548074229145bfe45454a5b5d3107), re-checked at [`a93ae870`](https://github.com/ElectronicBabylonianLiterature/ebl-api/commit/a93ae870e47f53883e06b8da565cfec9c7b8f8df) |
| Base | `master` @ `cd46110c` (merge base `2169b155`) |
| Size | 14 files, +676 / −7, 18 commits (was 22 files, +1277 / −7 at `6394de8d`) |
| Review date | 2026-09-23 |
| Previous review | `ad222eb3`, request changes (D1–D7); all addressed in `6394de8d` |
| GitHub state | Open, mergeable, review decision `CHANGES_REQUESTED` (Fabdulla1, 2026-08-18); Sourcery approved `6394de8d` |
| CI | All green on `a93ae870` (and on `6394de8d`): tests 3.11 / 3.12 / pypy-3.11, CodeQL, GitGuardian, Sourcery, qlty |
| qlty | "No blocking issues", coverage diff 100% |
| CodeQL | "No new alerts in code changed by this pull request" |
| Local gates | format ✅ · lint ✅ · pyre ✅ · pyright ✅ · mypy (changed files) ✅ · flake8 ✅ · full suite ✅ (4443 passed) · changed-module coverage 100% ✅ · lint-md ✅ |
| Runtime check | Real app against throwaway local Mongo, with null, `simple` and Redis cache backends |
| Dev container / config changes | **None** |
| New `.md` files | **None** at `a93ae870` (8 `TASK-*.md` files at `6394de8d`, removed; see R1). The `TASK-*.md` work notes are then committed back **on purpose** for handoff; delete them before merge |
| Verdict | **Approve**: the code is ready. The merge is waiting only on Fabdulla1's re-review (R2) |

## Review summary

This one's in good shape now. Every ID `/realia/all` lists opens at `/realia/{id}`, a malformed document can't take the endpoint down any more, and with the production Redis cache repeated calls cost one query every ten minutes. The only real problem was the task-tracking notes that slipped into the last commit, and `a93ae870` takes them out again. What's left is replying to Fabdulla1's review so it can be re-reviewed. 👍

## Summary

The PR adds `GET /realia/all`, which returns a sorted JSON array of Realia `_id`s for the frontend sitemap (`ebl-frontend` `RealiaRepository.listAllRealia` already calls it). The listing:

- leaves out redirect stubs, using the same rule as the frontend's `getRedirectTarget`;
- leaves out the reserved identifier `all`;
- keeps only string `_id`s and only documents `RealiaEntrySchema` can load, which is the same load `/realia/{id}` performs;
- guards every array access in the `$expr` with `$isArray`/`$cond`, so a legacy scalar or object can't fail the query;
- sorts case- and accent-insensitively, memoizes the list through the app cache for 600 s, and sends `Cache-Control: public, max-age=600` on every response.

All seven findings from the previous review (at `ad222eb3`) are fixed in code or in the PR description. The data hard gate isn't affected, since the response is a single array of string IDs. The largest changed `.py` file is 189 lines.

### Existing PR feedback

| # | Source | Comment | Thread state | Status at `a93ae870` |
| --- | --- | --- | --- | --- |
| 1 | Sourcery (inline, `realia_repository.py`) | Return domain objects, or make the ID-only intent explicit | Resolved | ✅ Renamed to `list_non_redirect_ids` |
| 2 | Sourcery (inline, `test_realia_route.py`) | Route test should prove sorting | Resolved, outdated | ✅ `test_list_returns_sorted_ids` seeds out of order |
| 3 | Sourcery (issue comment) | Reviewer's guide | n/a | ℹ️ Stale, describes the first iteration; no action needed |
| 4 | Sourcery (review, 2026-09-23) | Approved `6394de8d` | n/a | ✅ |
| 5 | Fabdulla1 (review, 2026-07-22) | `all` shadows an entry with `_id` `"all"` | n/a | ✅ Reserved in `reserved_identifiers.py` and documented in the PR description as an accepted constraint |
| 6 | Fabdulla1 (inline, `bootstrap.py`) | `ids` has the same collision; reserve it everywhere | **Unresolved**, outdated, no reply | ✅ Moot, the route is `all` again. ⚠️ Needs a reply (R2) |
| 7 | Fabdulla1 (inline, `realia_stub_filter.py`) | Guard `$size`/`$filter` with `$isArray`/`$cond` | **Unresolved**, no reply | ✅ `_as_array` plus the robustness tests. ⚠️ Needs a reply (R2) |
| 8 | Fabdulla1 (review, 2026-08-18, **CHANGES_REQUESTED**) | (a) explicit `null` treated as absent | n/a | ✅ Only schema-loadable entries are listed |
| 8 | ″ | (b) `Cache-Control` alone doesn't absorb repeated calls | n/a | ✅ `cache.memoize` (600 s), verified with Redis (R3) |
| 8 | ″ | (c) PR description is out of date | n/a | ✅ Rewritten and matches the code. ⚠️ No reply yet (R2) |

### Checks, qlty and CodeQL

- **CI checks:** all pass on `a93ae870` and on `6394de8d`. `docker` was skipped, which is normal for a PR.
- **CodeQL:** "No new alerts in code changed by this pull request". The code-scanning alerts API returns 403 for this token, so this comes from the check-run output.
- **qlty:** "No blocking issues", total coverage 96.4% (+0.5%), coverage diff 100%.

## Findings

| ID | Severity | Title | Status |
| --- | --- | --- | --- |
| R1 | High | Head commit added 8 `TASK-pr735-*.md` tracking files to the PR | ✅ Fixed in `a93ae870`; notes re-committed on purpose for handoff, ⚠️ delete before merge |
| R2 | Medium | Fabdulla1's review and both inline threads have no reply | ⏳ Open, replies drafted |
| R3 | Info | Server-side reuse depends on `CACHE_CONFIG` | ✅ Resolved, production uses Redis |
| R4 | Info | The detail route still returns 500 for entries the schema can't load (on master too) | ⏳ Fixed in [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767), open |
| R5 | Info | mypy errors and uncovered lines in untouched, imported code | ℹ️ No action in this PR |

### Details

#### R1 — Head commit added 8 `TASK-pr735-*.md` tracking files to the PR (High, fixed)

- **Where:** [`6394de8d`](https://github.com/ElectronicBabylonianLiterature/ebl-api/commit/6394de8d618548074229145bfe45454a5b5d3107) added `TASK-pr735-fixes-log.md`, `-fixes-todo.md`, `-handoff-log.md`, `-handoff-todo.md`, `-handoff.md`, `-review-log.md`, `-review-todo.md` and `-review.md` at the repo root (+601 lines).
- **What:** These are local work notes, not project docs. Merging would have put them in `master`. It's the fourth time they reached the branch (`1f8e85e8`, `924340f0` and `ad222eb3` each removed an earlier set).
- **Fix:** [`a93ae870`](https://github.com/ElectronicBabylonianLiterature/ebl-api/commit/a93ae870e47f53883e06b8da565cfec9c7b8f8df) removes exactly those 8 files (−601). The PR now has 14 files, and the only `.md` in it is the `README.md` change, which documents the `cache.cached` / `Cache-Control` interaction.
- **To stop it happening again:** stage files by name instead of `git add -A`, or add `TASK-*.md` to the local `.git/info/exclude`.
- **Handoff:** after this review, the `TASK-*.md` work notes (this review, the handoff and the task logs) were committed to the branch on purpose, so the next person has them. They are not project docs: delete them in a last commit before merging.

#### R2 — Fabdulla1's review and both inline threads have no reply (Medium, open)

- **Where:** the 2026-08-18 review (CHANGES_REQUESTED) and the inline threads on [`bootstrap.py`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/a93ae870e47f53883e06b8da565cfec9c7b8f8df/ebl/realia/web/bootstrap.py) and [`realia_stub_filter.py`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/a93ae870e47f53883e06b8da565cfec9c7b8f8df/ebl/realia/infrastructure/realia_stub_filter.py).
- **What:** Every point is addressed in code or in the PR description (see "Existing PR feedback"), but nothing on the PR says so. The review decision stays `CHANGES_REQUESTED` until Fabdulla1 re-reviews, and no re-review is requested.
- **Fix:** reply to the review and both threads, resolve the threads, and request a re-review. Replies are drafted and haven't been posted.

#### R3 — Server-side reuse depends on `CACHE_CONFIG` (Info, resolved)

- **Where:** [`realia.py:55-65`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/a93ae870e47f53883e06b8da565cfec9c7b8f8df/ebl/realia/web/realia.py#L55-L65).
- **What:** `cache.memoize` only helps when a cache backend is set, and the default is the null backend. Nothing in this repo sets one.
- **Resolution:** production sets `CACHE_CONFIG: '{"CACHE_TYPE": "redis", "CACHE_REDIS_HOST": "redis"}'` in `ElectronicBabylonianLiterature/infrastructure` `ebl.yml`. Tested locally with Redis and two app processes: 6 alternating requests made 1 `realia` query, both processes shared one memoize key (TTL 600), the bodies were identical, and every response had `Cache-Control: public, max-age=600`. No change needed.

#### R4 — The detail route still returns 500 for entries the schema can't load (Info, follow-up)

- **Where:** [`mongo_realia_repository.py:64-67`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/a93ae870e47f53883e06b8da565cfec9c7b8f8df/ebl/realia/infrastructure/mongo_realia_repository.py#L64-L67) (`_load_entry`), which `find` uses.
- **What:** `GET /realia/NullType` (`type: null`) → 500, `ValidationError: {'type': ['Field may not be null.']}`. The load path is the same on `master`, so this PR doesn't cause it, and `/realia/all` correctly leaves such entries out.
- **Fix:** out of scope here. Branch `fix-realia-detail-unloadable-entries` makes `RealiaEntrySchema` treat a top-level `null` as absent: `type: null` and `realiaId: null` now return 200. Wrong-shaped values like `relatedTerms: [5]` still return 500 and need a data cleanup. Opened as [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767). Its status: one CI run passed everything; the other hit a PyPy flake in an unrelated test (`PermissionError` starting the in-memory `mongod`). Sourcery's comment to check `Mapping` instead of `dict` in the new hook is still open.

#### R5 — mypy errors and uncovered lines in untouched, imported code (Info)

- **What:** mypy on the changed files reports 0 errors in them and 26 in 17 untouched modules they import (`ebl/transliteration`, `ebl/corpus`, …). All 26 are pre-existing on `master`. `test_realia_info.py` lines 26–35 (the fake's `find`/`search` stubs) are uncovered and come from `master` (`a238304d`). The line this PR adds there is covered.
- **Fix:** none in this PR.

## Severity

- **High:** R1, fixed.
- **Medium:** R2, a process blocker: the merge waits on Fabdulla1's re-review.
- **Info:** R3 (resolved), R4 (follow-up PR #767), R5 (pre-existing).

## Reproduction Steps

All steps use a local mongod on `127.0.0.1:27017` and throwaway databases. `.env` is never sourced.

1. Seed `realia` with healthy entries (`Anu`, `Ähre`, `TwoCross`, `a/b`), a redirect stub (`Pig`), the reserved `all`, malformed entries (`NullType` with `type: null`, `NullRealiaId`, `BadElement` with `relatedTerms: [5]`, `_id: 42`) and awkward IDs (`""`, `by-id`, `"trail "`, `q?x`, `50%`, `h#1`).
2. Serve `ebl.app:get_app` with `MONGODB_URI=mongodb://127.0.0.1:27017`, a throwaway `MONGODB_DB` and dummy Auth0/Sentry values.
3. `curl -i localhost:<port>/realia/all` → `200`, `Cache-Control: public, max-age=600`, body `["", "50%", "a/b", "Ähre", "Anu", "by-id", "h#1", "q?x", "trail ", "TwoCross"]`. `Pig`, `all`, the malformed entries and `42` are left out.
4. Request each listed ID, percent-encoded, at `/realia/{id}` → all `200`, and each body's `_id` matches.
5. `curl -i localhost:<port>/realia/NullType` → `500` with `ValidationError` (R4, same on `master`).
6. Start `redis:7-alpine` on `127.0.0.1:6379`, serve two processes with `CACHE_CONFIG='{"CACHE_TYPE": "redis", "CACHE_REDIS_HOST": "127.0.0.1"}'`, enable Mongo profiling and alternate 6 requests between them → 1 `realia` query (R3).
7. `gh pr view 735 --json files` at `a93ae870` → 14 files, no `TASK-*.md` (R1). After the handoff commit, the `TASK-*.md` notes show up again, as intended.

## Recommendation

**Approve.** The endpoint is correct, robust and cached, and it matches the frontend.

1. R2: reply to Fabdulla1's review and both threads, resolve the threads, and request a re-review.
2. R4: review and merge [#767](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/767).
3. Delete all `TASK-*.md` work notes in a last commit before merging. They're committed on purpose for handoff, but they must not reach `master`.
