<!-- markdownlint-disable MD013 -->

# PR #735 Review — Add GET /realia/all endpoint for listing Realia IDs for the sitemap

| Field | Value |
| --- | --- |
| PR | [#735](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735) |
| Title | Add GET /realia/all endpoint for listing Realia IDs for the sitemap |
| Author | Me (my PR) |
| Branches | `add-realia-slugs-endpoint` → `master` |
| Head SHA | `30a23b22ebc8af7f34a6c134de7547cb0b38a730` |
| Size | 14 files, +682 / −7 |
| Reviewed on | 2026-09-30 |
| Review triggering this pass | [Fabdulla1, CHANGES_REQUESTED, 2026-09-30](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735#pullrequestreview-5367106362) |
| Merge state | Mergeable, blocked by changes requested; branch is 12 commits behind `master` (incl. #767) |
| CI | All checks pass on the head commit (Test Python 3.11 / 3.12 / pypy-3.11, CodeQL analyze, GitGuardian, Sourcery); `docker` skipped |
| qlty | Check: no blocking issues. Coverage diff 100%, total 96.7% (+0.8%). Local `qlty smells --all --include-tests`: identical to `master`, no new findings |
| CodeQL | No new alerts in code changed by this PR |
| Dev container | **No changes** (`.devcontainer/`, Dockerfiles, compose untouched) |
| New `.md` files | **None** (only `README.md` modified) |
| Verdict | **Changes requested** — 2 medium correctness findings, 3 low, 1 nit, 2 process items |

## Review Summary

Thanks for the careful rounds on this, Fabdulla1 — it really has come a long way. I re-checked your latest points against a running API: the malformed `reallexikon.reference.id` case does get listed and then 500s on the detail route, and an `_id` like `by-id/foo` gets listed but opens a different entry, so both need a fix. The cache-staleness point is fair too, though low-impact for a sitemap. Everything else looks solid: type checkers, lint, qlty and coverage are all clean, and nothing touches the dev container. I'll also rebase onto `master` now that #767 is in, drop the stale "until #767" note from the description, and close out the two open threads.

## Summary

The PR adds `GET /realia/all`, returning a sorted list of Realia `_id`s for the frontend sitemap. It excludes redirect stubs (same rule as the frontend `getRedirectTarget`, confirmed against `ebl-frontend/src/realia/domain/RealiaEntry.ts`), the reserved `all` id, non-string `_id`s, and documents `RealiaEntrySchema` rejects. The list is memoized for 600 s and served with `Cache-Control: public, max-age=600`.

The central invariant the PR promises — "every ID it returns can be fetched back from `/realia/{id}`" — does not fully hold: schema loading is not the whole detail path (bibliography injection and routing can still fail or misroute). Two shapes break it, both reproduced on the running service.

## Findings

### Details

#### F1 — Listed entries whose detail route returns 500 (malformed `reallexikon.reference.id`)

- **Severity:** Medium
- **Where:** `ebl/realia/infrastructure/realia_loadability.py:6-11`, `ebl/realia/infrastructure/realia_schemas.py:24-36` (`ReallexikonReferenceField`), `ebl/realia/infrastructure/realia_stub_filter.py:61-75`, `ebl/realia/infrastructure/mongo_realia_repository.py:108` (`_collect_reference_ids`)
- **Problem:** `is_loadable` only runs `RealiaEntrySchema().load()`. `ReallexikonReferenceField._from_id` accepts any truthy `id` and wraps it in `BibliographyId(...)` without a type check. `/realia/{id}` then calls `_inject_bibliography`, which adds `rlex.reference.id` to a `set` → `TypeError: unhashable type` for an object or list id → HTTP 500. The Mongo stub filter also treats any non-empty `reference.id` (including objects) as "resolvable", so such a document is never treated as a stub either. An integer id loads and returns 200, but is still not a valid bibliography id.
- **Reproduction:** see Reproduction Steps, R1.
- **Fix:** Validate that the nested id is a string in the schema (`_from_id`: non-`str` → `ValidationError`, or treat as `None` if that is the intended legacy semantics), so `is_loadable` rejects it and the detail route 404s/422s instead of 500. Align `_is_resolvable_reference` in the stub filter with the same rule (`{"$eq": [{"$type": f"{reference}.id"}, "string"]}` and non-empty) so the list and the frontend's stub rule agree. Add the object/list/int `reference.id` shapes to `UNLOADABLE_DOCUMENTS` and to `test_every_listed_id_is_retrievable_despite_malformed_entries`.

#### F2 — `_id` beginning with `by-id/` is listed but resolves to a different entry

- **Severity:** Medium
- **Where:** `ebl/realia/web/bootstrap.py:22-25`, `ebl/realia/infrastructure/mongo_realia_repository.py:88` (`_build_listable_query`), `ebl/realia/domain/reserved_identifiers.py`
- **Problem:** Falcon decodes `%2F` before routing, so `/realia/by-id%2Ffoo` is routed to `RealiaByIdResource` with `realia_id="foo"`. The listing only excludes the exact id `all`, so an entry with `_id="by-id/foo"` is advertised but its URL returns whichever entry has `realiaId="foo"` (or 404). This is the same class of collision as `all`, just by prefix.
- **Reproduction:** see Reproduction Steps, R2.
- **Fix:** Reserve the prefix alongside the segment in `reserved_identifiers.py` (e.g. a `BY_ID_ROUTE_SEGMENT = "by-id"` used by `bootstrap.py`, plus a reserved-prefix check) and exclude `_id`s matching `^by-id/` in `_build_listable_query`, with a route-level test. A non-overlapping raw-id route would also work but is a larger change.

#### F3 — Empty `_id` is listed

- **Severity:** Low
- **Where:** `ebl/realia/infrastructure/mongo_realia_repository.py:88` (`_build_listable_query`)
- **Problem:** An entry with `_id=""` is listed. On the API side it is actually retrievable (`GET /realia/` returned it, 200), so Fabdulla1's "no detail segment" point does not reproduce here, but the sitemap would emit a bare `/realia/` URL, which on the frontend is the Realia search page, not an entry.
- **Fix:** Exclude empty ids in the query (`"_id": {"$type": "string", "$nin": [...], "$ne": ""}` or add `""` to the excluded set) and cover it in `test_realia_list_route.py`.

#### F4 — Two cache layers compound staleness to ~20 minutes

- **Severity:** Low
- **Where:** `ebl/realia/web/realia.py:55-65`
- **Problem:** The list is memoized for 600 s and every response carries a fresh `max-age=600` with no `Age` header. A value computed 599 s ago can be cached downstream for another 600 s, so the real bound is ~1200 s. Memoization itself works (an entry inserted after the first call was not listed until expiry).
- **Fix:** Either emit an `Age` header derived from the memoized timestamp, halve one of the two lifetimes, or document the ~2×600 s bound in the README caching section and the PR description. For a sitemap, documenting it is sufficient.

#### F5 — Mixed-type parametrize list

- **Severity:** Nit
- **Where:** `ebl/tests/realia/test_realia_list_loadability.py:35` (`NON_STRING_IDENTIFIERS = [42, 4.2, True, {"id": "x"}]`)
- **Problem:** The project's data-shape rule says one array holds exactly one data type. These are deliberately malformed fixture values, so the intent is clear, but the list still mixes int, float, bool and dict.
- **Fix:** Use `pytest.param(..., id="int")` entries or separate parametrize tables per type, if we want the test code to follow the rule to the letter.

#### P1 — Two review threads still unresolved

- **Severity:** Process
- [realia_stub_filter.py:54](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735#discussion_r3672279846) (`$isArray`/`$cond` guard): **addressed** in code — `_as_array` wraps every array field, and `test_realia_stub_filter_robustness.py` covers scalar/object shapes (a scalar `crossReferences` doc was correctly excluded at runtime). Reply and resolve.
- [bootstrap.py `ids` collision](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735#discussion_r3672261891) (outdated): the route is back at `/realia/all`, `all` is reserved in one place and excluded from the list, and the "reachable only via `/realia/by-id/{realiaId}`" limitation is documented as accepted in the description. Reply and resolve (F2 covers the remaining prefix collision).

#### P2 — Branch behind `master`; description has a stale note

- **Severity:** Process
- #767 (null optional fields) was merged on 2026-09-30, but the PR branch and GitHub's merge ref do not contain it, so CI has not run against it. Locally, the PR diff applies cleanly on current `master` (`c76ee0bb`) and all gates pass (see below).
- The description still says "until #767 is merged, an explicit `null` …"; that sentence is now outdated. After updating from `master`, drop it.

### Existing PR feedback

| Source | Date | Point | Status |
| --- | --- | --- | --- |
| Sourcery (review + inline) | 2026-07-03 | Repository returns raw ids; name should say so | Resolved — renamed `list_non_redirect_ids` |
| Sourcery (inline) | 2026-07-03 | Route test should prove sorting | Resolved — `test_list_returns_sorted_ids` seeds out of order |
| Sourcery | 2026-09-23 | Approved | Dismissed on later push; no new Sourcery findings |
| Fabdulla1 | 2026-07-22 | `/realia/all` shadows `_id="all"`; reserve or document | Addressed — reserved + excluded + documented |
| Fabdulla1 (inline) | 2026-07-29 | `/realia/ids` collides with `_id="ids"` | Outdated — see P1 |
| Fabdulla1 (inline) | 2026-07-29 | Guard `$size`/`$filter` with `$isArray` | Addressed in code — thread still open, see P1 |
| Fabdulla1 | 2026-08-18 | Explicit `null` fields break the invariant | Addressed — schema-loadability filter + #767 merged |
| Fabdulla1 | 2026-08-18 | `Cache-Control` alone does not cache server-side | Addressed — `cache.memoize` (verified at runtime) |
| Fabdulla1 | 2026-08-18 | Update the PR description | Mostly done — stale #767 note remains, see P2 |
| Fabdulla1 | 2026-09-30 | Empty `_id` / `by-id/…` ids | `by-id/…` confirmed (F2); empty id partly (F3) |
| Fabdulla1 | 2026-09-30 | Schema load ≠ detail success (`reference.id` object) | Confirmed (F1) |
| Fabdulla1 | 2026-09-30 | Compounded cache lifetimes | Confirmed (F4) |
| qlty / CodeQL / GitGuardian | — | — | No findings |

## Severity

| ID | Severity | Title |
| --- | --- | --- |
| F1 | Medium | Listed entries 500 on the detail route (malformed `reallexikon.reference.id`) |
| F2 | Medium | `by-id/…` ids listed but resolve to a different entry |
| F3 | Low | Empty `_id` listed |
| F4 | Low | Cache lifetimes compound to ~1200 s |
| F5 | Nit | Mixed-type parametrize list in a test |
| P1 | Process | Two unresolved review threads |
| P2 | Process | Branch behind `master`; stale #767 note in the description |

## Reproduction Steps

Setup used (local only, never the production cluster): PR diff applied on `origin/master` `c76ee0bb`; API started with `MONGODB_URI=mongodb://127.0.0.1:27017`, `MONGODB_DB=pr735_review`, `CACHE_CONFIG='{"CACHE_TYPE": "simple"}'`, `SENTRY_DSN=` via `poetry run waitress-serve --port=8001 --call ebl.app:get_app`.

**R1 (F1)** — seed:

```json
{"_id": "ObjectRefId", "reallexikon": [{"id": "r1", "reference": {"id": {"nested": 1}}}]}
{"_id": "ListRefId", "reallexikon": [{"id": "r1", "reference": {"id": ["a"]}}]}
```

`GET /realia/all` includes both ids. `GET /realia/ObjectRefId` → **500** (`TypeError: unhashable type: 'dict'`); `GET /realia/ListRefId` → **500** (`TypeError: unhashable type: 'list'`).

**R2 (F2)** — seed:

```json
{"_id": "by-id/foo", "type": ["x"], "realiaId": "R-slash"}
{"_id": "Other", "type": ["x"], "realiaId": "foo"}
```

`GET /realia/all` includes `"by-id/foo"`. `GET /realia/by-id%2Ffoo` → 200 with `"_id": "Other"`.

**R3 (F3)** — seed `{"_id": "", "type": ["x"]}`; `GET /realia/all` includes `""`.

**R4 (F4)** — `GET /realia/all` → `Cache-Control: public, max-age=600`, no `Age`. Insert a new entry; the next `GET /realia/all` does not include it (memoized), while `GET /realia/<new id>` → 200.

Also exercised and fine: ids with `?`, `#`, `%20`, a trailing `/` (all 200 when URL-encoded); redirect stub, `all` and a scalar `crossReferences` document all excluded.

## Recommendation

**Request changes.** Fix F1 and F2 (small, local changes plus tests), exclude the empty id (F3), and document or tighten the cache bound (F4). Then update the branch from `master`, drop the stale #767 sentence, and reply to/resolve the two open threads. F5 is optional polish.

Local gates run on the PR applied to current `master`:

| Gate | Result |
| --- | --- |
| `task format` | Pass |
| `task lint` (ruff) | Pass |
| `task type` (pyre) | Pass — no type errors |
| pyright 1.1.411 on the 13 changed `.py` files | Pass — 0 errors |
| `mypy --ignore-missing-imports` on changed files | Pass |
| `flake8 --max-line-length=120` on changed files | Pass |
| Coverage on the 8 changed source modules | 100% (210 realia tests pass) |
| `qlty smells --include-tests` (changed files, and repo-wide vs `master`) | No findings; repo-wide set identical to `master` |
| `task test` (full suite) | Pass — 5490 passed, 2 skipped, 1 xfailed, 0 failures |
| File length (≤ 250 lines) | Pass — largest changed file 189 lines |
| `task lint-md` | Pass — 0 errors (review file carries `markdownlint-disable MD013` by request) |

## Resolution (2026-09-30, uncommitted on `add-realia-slugs-endpoint`)

| ID | Status | Change |
| --- | --- | --- |
| F1 | Fixed | `ReallexikonReferenceField._from_id` returns `None` for a non-string id; the stub filter counts only a non-empty string `reference`/`reference.id` as resolvable. Tests: schema unit test, stub-filter params (int/object/list id, list reference), listed-and-retrievable route test |
| F2 | Fixed | `BY_ID_ROUTE_SEGMENT` and `RESERVED_REALIA_ID_PREFIXES = ("by-id/",)` in `reserved_identifiers.py`; the query excludes `^by-id/`; `bootstrap.py` builds the by-id route from the constant. Tests: prefix excluded, look-alikes (`by-id`, `by-idx/foo`, `a/by-id/foo`) still listed, route test with `by-id/foo` + `realiaId: foo` |
| F3 | Fixed | `EMPTY_IDENTIFIER` added to `RESERVED_REALIA_IDS` (covered by the existing reserved-id parametrised tests) |
| F4 | Fixed | Memoized value is a frozen `RealiaIdListing(computed_at, identifiers)`; the response sends `Age`, bounding total staleness to 600 s. README paragraph; freezegun test (Age 599 → expiry → 0) |
| F5 | Fixed | `NON_STRING_IDENTIFIERS` and the same pattern in `NON_ARRAY_VALUES` now hold `pytest.param` sets only |
| P1 | Drafted | Replies to both threads prepared; not posted |
| P2 | Pending your go-ahead | Updating from `master` needs a merge/rebase; new PR description drafted, not posted |

Also fixed in touched files: 62 pre-existing pyright errors in `test_realia_entry.py` (typed `load`/`dump` results) and 2 pyright override errors in `realia_schemas.py` (`attr_name` → `attr`, identical to master).

## Remaining work and next steps

1. Merge `master` into the branch (in progress in the same session; see `TASK-pr735-merge-log.md` for the result) and re-run every gate on the merged tree.
2. Push, then confirm CI, qlty and CodeQL are green on the new head.
3. Post the drafts below: the two thread replies (then resolve both threads), the response to review 5367106362, and the new PR description.
4. Re-request review from Fabdulla1.
5. Remove all `TASK-pr735-*` files from the branch before the PR is merged.

Nothing else from this review remains open in the code.

## GitHub drafts (not posted)

### Reply — stub filter `$isArray` thread (discussion_r3672279846)

Done: every array field now goes through `_as_array` (`$cond` + `$isArray`), so a scalar or object counts as an empty array instead of breaking `$size`/`$filter`. `test_realia_stub_filter_robustness.py` covers string, integer, object and boolean values in each field. Such documents are then also dropped by the schema-loadability check, so they can't reach the sitemap.

### Reply — `/realia/ids` collision thread (discussion_r3672261891)

The route is back at `/realia/all`. `all` is reserved in `reserved_identifiers.py` and excluded from the listing, and I've now also reserved the `by-id/` prefix and the empty id there. Since the API has no Realia write path, these can't be rejected at creation, so the description documents it as an accepted constraint (such entries remain reachable via `/realia/by-id/{realiaId}`).

### Response to review 5367106362

Thanks, all three points were spot on, and I reproduced each against a running API before fixing:

- **Non-string `reallexikon.reference.id` → 500:** the schema now treats a non-string id as no reference (like other unexpected shapes), and the stub filter only counts a non-empty *string* reference as resolvable, so the list, the detail route and the frontend's stub rule agree. Tests cover int/object/list ids.
- **`by-id/…` and empty `_id`s:** the `by-id/` prefix and `""` are now reserved in `reserved_identifiers.py` and excluded from the listing; the route test seeds `by-id/foo` next to an entry with `realiaId: foo` and checks every listed id opens its own entry.
- **Compounded cache lifetimes:** the memoized result now carries its computation time and the response sends `Age`, so total staleness stays within 600 s. There's a freezegun test for the bound, and the README explains the pattern.

I also updated the description (dropped the stale #767 note).

### New PR description

````markdown
Add `GET /realia/all`, returning a sorted JSON array of Realia `_id`s for frontend sitemap generation. `ebl-frontend` already calls it from `RealiaRepository.listAllRealia` (used by `src/router/sitemap.tsx`); backend master has no listing route, so that call currently 404s.

## What the endpoint returns

Every ID it returns can be fetched back from `/realia/{id}`. Excluded:

- **Redirect stubs** — the same rule as the frontend's `getRedirectTarget`: exactly one cross-reference and no own content, where own content means a non-empty `afoRegister`, `references` or `afoCrossReferences`, more than one `reallexikon` entry, or a `reallexikon` entry with a resolvable reference (a non-empty string reference or reference `id`; any other shape counts as no reference, matching the frontend where such a reference loads as `null`). `relatedTerms`, `type` and `wikidataId` are metadata, not content. Entries with two or more cross-references are listed (the frontend renders them rather than redirecting).
- **Reserved identifiers** — `all` collides with the route itself, an `_id` starting with `by-id/` is routed to `/realia/by-id/{realiaId}` (Falcon decodes `%2F` before routing) and would open a different entry, and an empty `_id` would put a bare `/realia/` (the frontend search page) into the sitemap. `ebl/realia/domain/reserved_identifiers.py` is the single source of truth for the route segments and the exclusions. The API has no Realia write path, so such entries cannot be rejected at creation; `all` and `by-id/…` entries are reachable only via `/realia/by-id/{realiaId}`. This is an accepted constraint.
- **Entries the detail route cannot load** — non-string `_id`s are filtered in Mongo; every remaining candidate is loaded through `RealiaEntrySchema` (the same load `/realia/{id}` performs) and skipped if it fails, e.g. elements of the wrong shape. A non-string `reallexikon[].reference.id` now loads as no reference instead of reaching bibliography injection, where it used to raise `TypeError` (500) on the detail route. One malformed document can no longer fail the whole endpoint.

Results are sorted case- and accent-insensitively, with the raw ID as a tie-breaker.

## Caching and performance

The stub filter is a `$expr` guarded with `$isArray`/`$cond`, so it cannot use an index; candidates are then schema-validated and sorted in Python. The result is memoized server-side through the app cache (`cache.memoize`, 600 s) and the response carries `Cache-Control: public, max-age=600` plus an `Age` header computed from the memoized timestamp, so downstream caches never keep a list for more than 600 s in total (without `Age`, the two lifetimes would add up to ~20 min), and the scan runs at most once per cache period when a cache backend is configured (`CACHE_CONFIG`; the default is the null backend). `cache.cached` is deliberately not used: on a cache hit it skips the responder hooks and drops the `Cache-Control` header. The response is unbounded by design, since a sitemap needs the complete list.

## Also in this PR

- The `/realia/{…}` URI template variable is renamed `realia_id` → `entry_id`, to distinguish the raw `_id` from `realiaId` (behaviour unchanged).
- `RealiaSearchResource` coerces a missing `query` to `""` (`or ""`) so the type checkers see a `str` (behaviour unchanged).
- The README's Caching section documents the `cache.cached` / `Cache-Control` interaction, the `cache.memoize` alternative, and the `Age` header that keeps the two lifetimes from compounding.
- `ReallexikonReferenceField` treats a non-string reference id as no reference, and its `_serialize`/`_deserialize` parameter is named `attr` like marshmallow's base (pyright override check).
- `test_realia_entry.py` types the schema `load`/`dump` results, clearing its pre-existing pyright errors.

## Summary by Sourcery

Add a cached Realia ID listing endpoint for reliable frontend sitemap generation.

New Features:
- Add `GET /realia/all` to return a complete, sorted list of loadable non-redirect Realia IDs for sitemap generation.
- Cache the generated ID list for 600 seconds and expose a public cache lifetime on responses.

Bug Fixes:
- Prevent malformed, reserved, non-string, or otherwise unreachable Realia entries from appearing in the listing, while ensuring individual invalid documents do not break the endpoint.

Enhancements:
- Centralize reserved Realia identifiers and align route parameter naming with the distinction between raw IDs and `realiaId`.
- Make redirect-stub detection and accent-insensitive ID ordering explicit and robust against malformed field values.

Documentation:
- Document the interaction between cached responses, responder hooks, and cache-control headers, including the memoization pattern used by the listing endpoint.

Tests:
- Add coverage for listing behavior, sorting, filtering, caching, retrievability, and malformed Realia documents.


````
