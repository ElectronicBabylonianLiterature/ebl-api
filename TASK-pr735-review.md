<!-- markdownlint-disable MD013 -->
# TASK-pr735 Review — PR #735 "Add GET /realia/all endpoint for listing Realia IDs for the sitemap"

| Field | Value |
| --- | --- |
| PR | [#735](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735) |
| Branch | `add-realia-slugs-endpoint` → `master` |
| Head reviewed | [`ad222eb3`](https://github.com/ElectronicBabylonianLiterature/ebl-api/commit/ad222eb356f312b5ba30ef2bfe28e26bac38a81e) |
| Base | `master` @ `cd46110c` (merge base `2169b155`; `master` has not touched `ebl/realia` or `ebl/cache` since) |
| Size | 12 files, +536 / −7, 16 commits |
| Review date | 2026-09-23 |
| GitHub state | Open, mergeable, blocked by review decision `CHANGES_REQUESTED` |
| CI | All green on `ad222eb3` (tests 3.11 / 3.12 / pypy-3.11, CodeQL, GitGuardian, qlty check, qlty coverage diff 100%) |
| Local gates | format ✅ · lint ✅ · pyre ✅ · pyright ✅ · mypy (changed files) ✅ · flake8 ✅ · full suite ✅ (4416 passed) · changed-module coverage 100% ✅ |
| Runtime check | Real app served locally against a throwaway Mongo database; 2 findings reproduced end to end |
| Dev container / config changes | **None** |
| New `.md` files | **None** |
| Verdict | **Request changes**: 2 Medium, 2 Low, 3 Nit/Info |
| Fix status | D1, D2, D3, D5 fixed in code; D4, D6, D7 drafted, not yet posted. See "Status after fixes" and `TASK-pr735-handoff.md` |

## Status after fixes (2026-09-23)

| ID | Status | How |
| --- | --- | --- |
| D1 | ✅ Fixed | Only entries that `RealiaEntrySchema` can load are listed (`realia_loadability.py`); `realia_document_shape.py` and its `null`-as-absent rule are gone |
| D2 | ✅ Fixed | `_id` must be a string in the Mongo query; schema-rejected element shapes, `null` fields and `realiaId: null` are no longer listed; tests in `test_realia_list_loadability.py` |
| D3 | ✅ Fixed | The ID list is memoized server-side (`cache.memoize`, 600 s); `Cache-Control` is still sent on every response. `cache.cached` was tried and rejected because cache hits drop the header |
| D4 | 📝 Drafted | New PR description is in `TASK-pr735-fixes-log.md` ("Drafts"); not posted |
| D5 | ✅ Fixed | `test_fake_repository_does_not_list_ids` covers the fake method |
| D6 | 📝 Drafted | Replies to both open threads are in `TASK-pr735-fixes-log.md`; not posted, threads still unresolved |
| D7 | 📝 Drafted | Covered by the "Also in this PR" part of the drafted description |

Re-verified on the running service: every listed ID returns 200, a numeric `_id` no longer breaks the endpoint, and six requests made one database query with a cache backend configured.

## Quick take

Nice work, this is close. The stub rule now matches the frontend's `getRedirectTarget` exactly, the `$isArray`/`$cond` hardening is solid, and every gate passes. Two things still break the PR's own promise that every listed ID opens: an explicit `null` in an array field still gets listed and then returns 500 (Fabdulla1 is right), and a single non-string `_id` makes the whole endpoint return 500. The cache and PR-description points also still need an answer. Fix those and I'm happy to approve. 🙂

## Summary

The PR adds `GET /realia/all`, which returns a sorted JSON array of Realia `_id`s for the frontend sitemap (`ebl-frontend` `RealiaRepository.listAllRealia` already calls `/realia/all`). The Mongo query excludes:

- reserved identifiers (`all`);
- redirect stubs, meaning entries with exactly one cross-reference and no own content;
- documents where an expected array field holds a scalar or object.

IDs are sorted in Python, case- and accent-insensitively, and the response sets `Cache-Control: public, max-age=600`.

What works:

- **Frontend parity.** The redirect rule matches `hasOwnContent`/`getRedirectTarget` in `ebl-frontend` `master` (`src/realia/domain/RealiaEntry.ts`). The own-content signals are `afoRegister`, `references`, `afoCrossReferences`, `reallexikon.length > 1`, or any resolvable reallexikon reference. An entry redirects only if it has no own content and exactly one cross-reference.
- **Route precedence.** `/realia/all` takes precedence over `/realia/{entry_id}` and the sink. IDs containing `/` still resolve through the sink (checked at runtime).
- **Robustness.** A scalar or object in any array field no longer causes a 500. `test_realia_stub_filter_robustness.py` covers this well.
- **Gates.** Code quality and every gate are fine. The data hard gate (one type per array) is not affected, since the response is a single array of string IDs. The largest changed file is 181 lines.

What doesn't work yet: the "every listed ID can be fetched from `/realia/{id}`" invariant still leaks, and in one case the leak takes down the whole endpoint.

### Existing PR feedback

| # | Source | Comment | Thread state | Status at `ad222eb3` |
| --- | --- | --- | --- | --- |
| 1 | Sourcery (inline, `realia_repository.py`) | Return domain objects, or rename to make the ID-only intent clear | Resolved | ✅ Addressed: renamed to `list_non_redirect_ids` |
| 2 | Sourcery (inline, `test_realia_route.py`) | Route test should prove sorting, not insertion order | Resolved, outdated | ✅ Addressed: `test_list_returns_sorted_ids` seeds out of order |
| 3 | Sourcery (issue comment) | Reviewer's guide | n/a | ℹ️ Stale: describes the first iteration (unfiltered `get_all_values`), no action needed |
| 4 | Fabdulla1 (review, 2026-07-22) | `all` shadows an entry with `_id` `"all"`; reserve it or document it | n/a | ✅ Mostly addressed: `all` is excluded from the listing via `RESERVED_REALIA_IDS`. See D6 for the remaining documentation point |
| 5 | Fabdulla1 (inline, `bootstrap.py`) | `ids` has the same collision; reserve across creation/import paths | **Unresolved**, outdated | ⚠️ Moot for `ids` (the route went back to `all`). The API has no Realia write path, so listing-time exclusion is the only enforcement possible here. Needs a reply and resolving (D6) |
| 6 | Fabdulla1 (inline, `realia_stub_filter.py`) | Guard `$size`/`$filter` with `$isArray`/`$cond` against scalar/object legacy values | **Unresolved** | ✅ Addressed in code (`_as_array`, `realia_document_shape.py`, robustness tests). Thread needs a reply and resolving |
| 7 | Fabdulla1 (review, 2026-08-18, **CHANGES_REQUESTED**) | (a) `null` treated as absent although the schema rejects it | n/a | ❌ **Still open**: confirmed at runtime → D1 |
| 7 | ″ | (b) `Cache-Control` alone does not absorb repeated calls; use `cache.cached(...)` or fix the description | n/a | ❌ **Still open**: confirmed with the Mongo profiler → D3 |
| 7 | ″ | (c) PR description no longer matches the code | n/a | ❌ **Still open** → D4 |

### Checks, qlty and CodeQL

- **CI checks:** all pass on `ad222eb3`. `docker` and `Sourcery review` were skipped (expected for a PR).
- **CodeQL:** "No new alerts in code changed by this pull request". The code-scanning alerts API returns 403 for this token, so I used the check-run output.
- **qlty:** "No blocking issues", coverage diff 100%. The issue page on qlty.sh requires a login, so I ran `qlty check` / `qlty smells` locally on the changed files:
  - 40 × bandit `B101` (assert in tests). This is the repo-wide test convention; untouched `test_realia_route.py` has 32 of the same.
  - 7 × qlty-mypy `call-arg` on `CollatedFieldQuery` / `RealiaEntry` constructors. These are false positives from qlty's mypy running without the project's attrs setup: the project's own mypy is clean on these files, and the flagged `mongo_realia_repository.py` lines 107–108 are pre-existing code outside the diff.
  - No smells.

## Findings

| ID | Severity | Title | Blocking |
| --- | --- | --- | --- |
| D1 | Medium | Explicit `null` in an array field is listed, then `/realia/{id}` returns 500 | Yes |
| D2 | Medium | A non-string `_id` makes all of `/realia/all` return 500; other malformed shapes are still listed | Yes (the `_id` part) |
| D3 | Low | No server-side caching; every request is a full `$expr` collection scan | Fix or reword |
| D4 | Low | PR description (and Sourcery guide) describe superseded behaviour | Yes (process) |
| D5 | Nit | Fake `list_non_redirect_ids` in `test_realia_info.py` is an uncovered added line | No |
| D6 | Info | Entry with `_id` `"all"` is permanently unreachable at `/realia/all`; unresolved threads need replies | No |
| D7 | Nit | Unrelated changes (`or ""` in search, `realia_id` → `entry_id` rename) not mentioned in the description | No |

### Details

#### D1 — Explicit `null` in an array field is listed, then `/realia/{id}` returns 500 (Medium)

- **Where:** [`realia_document_shape.py:3`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/infrastructure/realia_document_shape.py#L3): `ABSENT_TYPES = ("missing", "null")`.
- **What:** The shape guard treats BSON `null` like a missing field. `RealiaEntrySchema` declares every array as `fields.List(..., load_default=list)`, and `load_default` applies only when the key is **absent**. An explicit `null` raises `ValidationError: Field may not be null`, so an entry like `{"_id": "X", "type": null}` is listed and its detail page returns 500. This breaks the invariant the PR states ("every ID it returns can be fetched back"), and it is exactly the case Fabdulla1 raised on 2026-08-18.
- **Evidence:** Runtime: `NullType` (`type: null`) is listed, and `GET /realia/NullType` → 500 with `marshmallow.exceptions.ValidationError: {'type': ['Field may not be null.']}`. `test_null_own_content_field_does_not_break_listing` only covers the redirect-shaped case, which is excluded anyway, so the suite doesn't catch this.
- **Fix:** Pick one:
  - (a) Use `ABSENT_TYPES = ("missing",)` so `null` counts as malformed and the entry is not listed.
  - (b) Better for users: make the schema tolerate `null` (e.g. a pre-load hook that drops `None` values for the list fields), so these entries become viewable and stay listed.

  Either way, add a route-level test that seeds a **non-stub** entry with `null` in each `ARRAY_FIELDS` member and asserts that every listed ID returns 200.

#### D2 — A non-string `_id` makes all of `/realia/all` return 500; other malformed shapes are still listed (Medium)

- **Where:** [`mongo_realia_repository.py:84-100`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/infrastructure/mongo_realia_repository.py#L84-L100), [`realia_id_sorting.py:13-17`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/infrastructure/realia_id_sorting.py#L13-L17).
- **What:**
  1. **Whole-endpoint failure.** `_id` is not type-checked. A single document with a numeric (or ObjectId) `_id` reaches `unicodedata.normalize` and raises `TypeError`, so the entire endpoint returns 500. That is the same "one bad document takes down the sitemap" failure the PR's robustness section sets out to prevent. Any such document would also fail `RealiaEntrySchema` (`id = fields.String`), so it should never be listed anyway.
  2. **Per-entry leaks (same invariant as D1).** The guard only checks the top-level type of the array fields. These entries are still listed and then return 500:
     - `realiaId: null`
     - a wrong element type (`relatedTerms: [5]`)
     - a cross-reference object missing `lemma` in an entry with two or more cross-references (this follows from `lemma` being required in the schema; I didn't reproduce it at runtime)
- **Evidence:** Runtime:
  - After inserting `{"_id": 42, ...}`, `GET /realia/all` → 500 with `TypeError: normalize() argument 2 must be str, not int`.
  - `NullRealiaId` is listed, and its detail route → 500 (`realiaId: Field may not be null`).
  - `BadElement` is listed, and its detail route → 500 (`relatedTerms: {0: Not a valid string}`).
- **Fix:**
  - Add `"$type": "string"` to the `_id` condition (`{"_id": {"$type": "string", "$nin": [...]}}`), plus a test with a numeric `_id`.
  - For the element-level leaks, pick one:
    - (a) Make the guarantee exact by projecting the documents and keeping only those that `RealiaEntrySchema().validate(...)` accepts. This costs more per request, which D3 would absorb.
    - (b) Reword the PR description so the invariant covers top-level array shapes only.

#### D3 — No server-side caching; every request is a full `$expr` collection scan (Low)

- **Where:** [`realia.py:52-58`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/web/realia.py#L52-L58).
- **What:** `cache_control(...)` only sets the response header. The responder is not wrapped in `cache.cached(...)`, so the Falcon-Caching middleware never stores it, whatever `CACHE_CONFIG` is (the default is the null backend). The PR description says `Cache-Control` "absorbs repeated calls", but that only holds if a shared HTTP cache sits in front of the API, and nothing in this repo sets one up. Each direct request does a non-indexable `$expr` scan, loads every ID into memory, and sorts in Python. Fabdulla1 raised this too.
- **Evidence:** With Mongo profiling at level 2, three `GET /realia/all` calls produced three `realia` queries.
- **Fix:** Pick one:
  - Follow the existing pattern: `cache_control([...])` together with `@cache.cached(timeout=DEFAULT_TIMEOUT)`, as in [`fragment_signs_resources.py:19`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/fragmentarium/web/fragment_signs_resources.py#L19). This needs `context.cache` passed into the route factory.
  - Or reword the "Performance trade-off" paragraph to say that caching depends on an upstream HTTP cache.

#### D4 — PR description (and Sourcery guide) describe superseded behaviour (Low)

- **Where:** PR body.
- **What:**
  - "Redirect stubs" lists `relatedTerms`, `type` and `wikidataId` as own content. Commit `198eacc0` removed those and added `reallexikon.length > 1`, so the description now contradicts the code (the code is right; it matches the frontend).
  - "Malformed legacy documents … are skipped, because `RealiaEntrySchema` cannot load them" overstates the guarantee (D1, D2).
  - The "absorbs repeated calls" claim is covered in D3.
  - The Sourcery reviewer's guide still describes the unfiltered first iteration. That is informational only.

  Fabdulla1 asked for the description to be updated before merge.
- **Fix:** Rewrite the "What the endpoint returns" section to match `realia_stub_filter.py` and state the frontend parity with `getRedirectTarget`. Update the robustness and caching paragraphs after D1–D3.

#### D5 — Fake `list_non_redirect_ids` in `test_realia_info.py` is an uncovered added line (Nit)

- **Where:** [`test_realia_info.py:36-37`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/tests/fragmentarium/test_realia_info.py#L36-L37).
- **What:** The merge with `master` required implementing the new abstract method on `FakeRealiaRepository`, which is correct. The added `raise NotImplementedError()` is never executed. `.coveragerc` omits `ebl/tests/*`, so neither CI nor qlty sees it, but under the "every added line at 100%" rule it is an uncovered line. The existing `search`/`find` stubs next to it (lines 25–34) are uncovered as well.
- **Fix:** Optional. Either accept it as a test double (the rule arguably targets production code), or add a one-line test asserting that the fake raises.

#### D6 — Entry with `_id` `"all"` is permanently unreachable at `/realia/all`; unresolved threads need replies (Info)

- **Where:** [`bootstrap.py:21`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/web/bootstrap.py#L21), [`reserved_identifiers.py`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/domain/reserved_identifiers.py).
- **What:** Excluding `all` keeps the sitemap correct, but a real entry named `all` could only be reached via `/realia/by-id/{realiaId}`, and only if it has a non-empty `realiaId`. The API has no Realia write path (the collection is imported), so this repo can't reject such an entry at creation time. Documenting the reservation where the Realia import lives would close the loop.
- **Fix:** Reply to and resolve Fabdulla1's two open inline threads:
  - `bootstrap.py`: moot, since the route is `all` again, reserved via `RESERVED_REALIA_IDS`, and there is no API write path.
  - `realia_stub_filter.py`: addressed by `_as_array` and the robustness tests.

  Optionally add a line to the PR description documenting the `all` reservation as an accepted constraint.

#### D7 — Unrelated changes not mentioned in the description (Nit)

- **Where:** [`realia.py:47`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/web/realia.py#L47) (`req.get_param(...) or ""`); [`realia.py:12`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/web/realia.py#L12) / [`bootstrap.py:23-25`](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/ad222eb356f312b5ba30ef2bfe28e26bac38a81e/ebl/realia/web/bootstrap.py#L23-L25) (URI template variable `realia_id` → `entry_id`).
- **What:** Both are harmless and behaviour-preserving: the rename separates the raw `_id` from `realiaId`, and `or ""` narrows `Optional[str]` for the type checkers. Neither is mentioned in the PR body.
- **Fix:** Mention them in one line in the description.

## Severity

- **High:** none.
- **Medium (blocking):** D1, D2. Both break the endpoint's stated contract, and D2 can fail the whole sitemap.
- **Low:** D3 (performance/claim accuracy) and D4 (description accuracy, explicitly requested by Fabdulla1).
- **Nit/Info:** D5, D6, D7.

## Reproduction Steps

All steps use a local mongod on `127.0.0.1:27017` and a throwaway database. `.env` is never sourced.

1. Seed `ebl_review_pr735.realia` with:
   - `{"_id": "Anu", "type": ["Divine names"], "crossReferences": []}`
   - `{"_id": "Pig", "crossReferences": [{"id": "Anu", "lemma": "Anu"}], "type": ["Animals"]}`
   - `{"_id": "all", "type": ["Reserved"]}`
   - `{"_id": "NullType", "crossReferences": [], "type": null}`
   - `{"_id": "NullRealiaId", "crossReferences": [], "realiaId": null}`
   - `{"_id": "BadElement", "crossReferences": [], "relatedTerms": [5]}`
2. Serve `ebl.app:get_app` with `MONGODB_URI=mongodb://127.0.0.1:27017`, `MONGODB_DB=ebl_review_pr735` and dummy Auth0/Sentry values.
3. Run `curl -i localhost:<port>/realia/all`. Expect `200`, `Cache-Control: public, max-age=600`, and a body that contains `NullType`, `NullRealiaId` and `BadElement`, but not `Pig` or `all`.
4. Run `curl -i localhost:<port>/realia/NullType` (and likewise for the other two). Expect `500` with a `ValidationError` in the server log. **(D1, D2)**
5. Insert `{"_id": 42, "crossReferences": [], "type": ["x"]}`, then run `curl -i localhost:<port>/realia/all`. Expect `500` with `TypeError: normalize() argument 2 must be str, not int`. **(D2)**
6. Enable profiling (`db.setProfilingLevel(2)`), call `/realia/all` three times, and count the `realia` query ops. Expect `3`. **(D3)**

## Recommendation

**Request changes.** The design is right, and the frontend alignment in `198eacc0` was the hard part. To get this over the line:

1. D1: stop treating explicit `null` as absent, or make the schema tolerate it. Add a route-level "every listed ID returns 200" test with `null` fields on a non-stub entry.
2. D2: add `"$type": "string"` to the `_id` filter plus a test. Decide whether the invariant should be exact (schema-validate) or documented as covering top-level shapes only.
3. D3: add `@cache.cached(timeout=DEFAULT_TIMEOUT)` or reword the caching claim.
4. D4: refresh the PR description to match the final rule and guarantees.
5. D6: reply to and resolve Fabdulla1's two open inline threads.

D5 and D7 are optional polish. Remember to delete the `TASK-pr735-*.md` tracking files before merge.
