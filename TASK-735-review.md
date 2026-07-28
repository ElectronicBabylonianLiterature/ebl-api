# TASK-735 Review — PR #735: Realia ID listing endpoint

- PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735>
- Branch: `add-realia-slugs-endpoint` -> `master`
- Commit reviewed: `1f8e85e8`
- Status: all findings addressed in the working tree; awaiting commit

## Summary

The PR adds an endpoint listing Realia IDs, backed by a new
`RealiaRepository.list_non_redirect_ids()` abstract method, a Mongo
implementation that filters out redirect stubs via an `$expr` query, and
a `RealiaListResource` Falcon resource.

The original review raised eight findings, two of them blocking. All
eight are now addressed. The endpoint moved from `/realia/all` to
`/realia/ids`, the stub filter now recognises three further content
fields and applies one uniform reallexikon rule, ordering is
accent- and case-insensitive, the resource sets a public cache
directive, and the query builder and sort key were extracted into
focused modules that also brought every test file well under the
250-line cap.

### Feedback fetched (mandatory gate)

| Source | Count | State |
| --- | --- | --- |
| `pulls/735/reviews` | 2 | 1 `COMMENTED` (Sourcery), 1 `CHANGES_REQUESTED` |
| `pulls/735/comments` | 2 | both Sourcery, both threads resolved |
| `issues/735/comments` | 1 | Sourcery Reviewer's Guide |
| Review threads (GraphQL) | 2 | both `isResolved: true` |
| Merged-in branch PRs | 0 | branch is linear from `51ec7945`, no merges |

### CI and qlty status at review time

All 17 checks passed on `1f8e85e8`: Test Python 3.11 / 3.12 / pypy-3.11,
CodeQL, Analyze (python), GitGuardian, Sourcery review; `docker`
skipped. `qlty check` — "No blocking issues"; `qlty coverage` 95.5%
(+0.1%); `qlty coverage diff` 100.0% against a 75% threshold.

## Findings

### 1. Reviewer's `CHANGES_REQUESTED` was unaddressed

Fabdulla1 requested changes on 2026-07-22; the newest commit was
`1f8e85e8` dated 2026-07-13, so nothing in the PR responded. The request:
`/realia/all` shadows any Realia entry whose `_id` is `"all"`, `"all"` is
not reserved, and not every entry has a non-empty `realiaId` fallback.

Falcon prefers the literal `/realia/all` segment over the
`/realia/{realia_id}` template regardless of registration order, so the
collision was permanent. Worse,
`test_list_non_redirect_ids_shadows_entry_named_all` asserted the
shadowing as correct, converting an open question into a locked-in
contract. Reserving `"all"` on write is not enforceable here: this
service exposes no Realia write path.

**Severity: High (blocking).**

**Resolution.** Route moved to `/realia/ids`
([bootstrap.py:20](ebl/realia/web/bootstrap.py#L20)). `"all"` is an
ordinary ID again; the shadowing test is replaced by
`test_entry_named_all_is_reachable`
([test_realia_ids_route.py:52](ebl/tests/realia/test_realia_ids_route.py#L52)),
which asserts `GET /realia/all` returns the entry document.

### 2. Entries carrying only `relatedTerms` / `type` / `wikidataId` were dropped

The own-content check inspected only `afoRegister`, `references`,
`afoCrossReferences`, and `reallexikon`, but `RealiaEntry` also carries
`related_terms`, `type`, and `wikidata_id`. An entry with one
cross-reference plus any of those was classified as a redirect stub and
vanished from the listing.

**Severity: High (blocking).**

**Resolution.** All six array fields now drive one uniform check via
`OWN_CONTENT_ARRAY_FIELDS`
([realia_stub_filter.py:6-13](ebl/realia/infrastructure/realia_stub_filter.py#L6-L13)),
with a parametrised test per field
([test_realia_list_ids.py:68-84](ebl/tests/realia/test_realia_list_ids.py#L68-L84)).

### 3. Placeholder-reallexikon heuristic was inconsistent

`PLACEHOLDER_REALLEXIKON_COUNT = 1` meant one unresolvable `reallexikon`
entry counted as no content (entry dropped) while two counted as content
(entry kept), with no stated reason.

**Severity: Medium.**

**Resolution.** The count rule is removed. `reallexikon` now counts as
own content only when at least one entry has a resolvable reference.
Parametrised tests cover both directions
([test_realia_list_ids.py:87-118](ebl/tests/realia/test_realia_list_ids.py#L87-L118)).
This deliberately reclassifies the "Has two reallexikon" case from
listed to stub; the change was approved before the assertion was moved.

### 4. Endpoint name did not match endpoint behaviour

The route was `/realia/all` but the implementation is
`list_non_redirect_ids` and returns a filtered subset. There is no
OpenAPI document for realia (`docs/openapi/` holds only
`ebl-partner-bibliography.v1.yaml`), so the route name is the only
contract signal a client has.

**Severity: Medium.**

**Resolution.** Folded into finding 1: `/realia/ids` no longer promises
completeness.

### 5. Sort order was code-point, not locale-aware

`sorted()` ordered by Unicode code point, so IDs `Zikkurat`, `Ähre`,
`apsu`, `Adad` came back as `['Adad', 'Zikkurat', 'apsu', 'Ähre']` —
every lowercase and umlaut initial after all uppercase ASCII. Realia
lemmata are German, so umlaut headwords are expected.

**Severity: Medium.**

**Resolution.** `sort_realia_ids`
([realia_id_sorting.py](ebl/realia/infrastructure/realia_id_sorting.py))
sorts on an NFKD-decomposed, combining-mark-stripped, case-folded key —
DIN 5007-1 style, no new dependency — with the original string as a
tie-break so equivalent IDs stay deterministic. IDs are returned
verbatim; only ordering changes. Both properties are tested
([test_realia_list_ids.py:45-66](ebl/tests/realia/test_realia_list_ids.py#L45-L66)).

### 6. Unbounded full collection scan, no cache directive

`$expr` predicates cannot use an index, so each request is a COLLSCAN
plus an in-process sort over the whole collection, with no limit. The
resource set no cache directive.

**Severity: Low.**

**Resolution.** `RealiaListResource.on_get` now carries
`@cache_control(["public", f"max-age={DEFAULT_TIMEOUT}"])`
([realia.py:56](ebl/realia/web/realia.py#L56)), matching
[fragment_search.py:65](ebl/fragmentarium/web/fragment_search.py#L65)
and [statistics.py:19](ebl/fragmentarium/web/statistics.py#L19), with a
test asserting the response header. The scan itself is unchanged — it is
correct, and caching removes the repeat cost.

### 7. qlty S1192 — duplicated `"$ifNull"` literal

`qlty check` flagged the literal `$ifNull` repeated three times.

**Severity: Low.**

**Resolution.** Extracted as `IF_NULL`
([realia_stub_filter.py:4](ebl/realia/infrastructure/realia_stub_filter.py#L4)).
`qlty check --upstream=master` now reports only `bandit:B101` asserts in
test files.

### 8. Test files were near the 250-line hard cap

`test_realia_route.py` was 246 lines and `test_realia_repository.py` 234.

**Severity: Low (advisory).**

**Resolution.** The listing tests moved into
`test_realia_list_ids.py` (151) and `test_realia_ids_route.py` (75);
the two originals dropped to 198 and 151. Largest file in the changed
set is now 198 lines.

### Prior feedback — dispositions

- **Sourcery comment 1** (return domain objects or rename
  `list_all_realia`): addressed in `1f8e85e8` by renaming to
  `list_non_redirect_ids`; thread resolved. Agreed, kept.
- **Sourcery comment 2** (assert sorted IDs, not insertion order):
  addressed; the successor test
  `test_list_ids_returns_sorted_ids` seeds `Pig, Anu, Enlil, Ellil` and
  asserts the sorted result. Agreed, kept.
- **`bandit:B101` (20 occurrences)**: `assert` in pytest tests is the
  intended idiom and qlty cloud does not block on it. Acknowledged, no
  action.
- **Fabdulla1 `CHANGES_REQUESTED`**: resolved — see finding 1.

## Severity

| # | Finding | Severity | State |
| --- | --- | --- | --- |
| 1 | Unaddressed `CHANGES_REQUESTED`; shadowing locked in | High | Fixed |
| 2 | `relatedTerms` / `type` / `wikidataId` entries dropped | High | Fixed |
| 3 | Inconsistent placeholder-reallexikon heuristic | Medium | Fixed |
| 4 | Route name did not match filtered behaviour | Medium | Fixed |
| 5 | Code-point sort order, not locale-aware | Medium | Fixed |
| 6 | Unbounded COLLSCAN per request, no cache directive | Low | Fixed |
| 7 | qlty S1192 duplicated `"$ifNull"` literal | Low | Fixed |
| 8 | Test files near the 250-line cap | Low | Fixed |

## Reproduction Steps

Findings 2, 3 and 5 were reproduced against `1f8e85e8` with a temporary
probe module placed in `ebl/tests/realia/` and removed afterwards. Each
now has a permanent regression test, listed under its resolution.

### Finding 2 — content-bearing entry dropped

```python
insert_stored(realia_repository, {
    "_id": "Has relatedTerms and type and wikidataId",
    "crossReferences": [{"id": "Canonical", "lemma": "Canonical"}],
    "relatedTerms": ["Schwein", "Sau"],
    "type": ["animal"],
    "wikidataId": ["Q787"],
})
realia_repository.list_non_redirect_ids()
```

Before: `[]`. After: `["Has relatedTerms and type and wikidataId"]`.

### Finding 3 — one placeholder dropped, two kept

Two entries, each with one cross-reference; the first with a single
`reallexikon` entry whose `reference` is `None`, the second with two such
entries.

Before: `['Two placeholders']`. After: `[]` — both are stubs.

### Finding 5 — ordering

Insert IDs `Zikkurat`, `Ähre`, `apsu`, `Adad`.

Before: `['Adad', 'Zikkurat', 'apsu', 'Ähre']`.
After: `['Adad', 'Ähre', 'apsu', 'Zikkurat']`.

### Finding 1 — route shadowing

With an entry whose `_id` is `"all"` stored:

Before: `GET /realia/all` returned the ID list; the entry was
unreachable through `/realia/{realia_id}`.
After: `GET /realia/all` returns the entry; the list moved to
`GET /realia/ids`.

## Verification performed

Re-run after every change:

| Gate | Command | Result |
| --- | --- | --- |
| Format | `task format` | 733 files formatted, no diff |
| Lint (ruff) | `task lint` | All checks passed |
| Tests (realia) | `pytest ebl/tests/realia` | 91 passed |
| Tests (full) | `task test` | 3808 passed, 2 skipped, 1 xfailed |
| Coverage | `--cov=ebl/realia --cov-report=term-missing` | 100%, 0 missing |
| Lint | `flake8 <changed> --max-line-length=120` | clean |
| Types (mypy) | `mypy <changed>` | 0 errors in changed files |
| Types (pyre) | `task type` | No type errors found |
| Types (pyright) | `npx pyright <changed>` | 0 errors in changed files |
| File size | `wc -l` on all changed `*.py` | max 198, cap 250 |
| qlty | `qlty check --upstream=master` | only `B101` in tests |
| Markdown | `task lint-md` | 0 errors |

`mypy` reports 51 errors across 25 files, all in modules pulled in
transitively (`ebl/bibliography/...`, `ebl/corpus/...`,
`ebl/ebl_ai_client.py`). None are in the files this PR touches and none
are introduced by it; they are pre-existing on `master` and outside this
PR's scope.

`pyright` initially reported 5 errors in two of the changed files —
`Schema.load` results flowing into `List[RealiaEntry]` parameters, and
`Request.get_param` being typed `Optional[str]` despite a default. All
five were confirmed pre-existing on `master` but were fixed here, since
they sit in files this PR touches: the schema loads now use `cast`
(matching `mongo_sign_repository.py:168`), and the query parameter falls
back with `or ""`, which makes the type true at runtime rather than
asserting it. Pyright reports 0 errors across the 10 changed files.

Pyright also reports 102 errors in `realia_schemas.py`,
`test_realia_cross_references.py`, and `test_realia_entry.py`. None of
those files is in this PR's diff; fixing them would widen the change
well beyond this review and is left for separate work.

## Recommendation

**Approve once committed.** Every finding is resolved and all hard gates
pass locally.

Two things to flag when the branch is pushed:

1. The endpoint path changed from `/realia/all` to `/realia/ids`. Any
   frontend work already written against `/realia/all` must be updated;
   the backend schema is the contract authority, so the client aligns to
   this path rather than the backend keeping an alias.
2. Response ordering changed from code-point to accent- and
   case-insensitive. If the client re-sorts the list itself, its
   comparator should match, or the two orderings will disagree.

## Cleanup reminder

`TASK-735-todo.md`, `TASK-735-log.md`, and `TASK-735-review.md` are task
tracking artifacts and must be removed before this PR is merged.
