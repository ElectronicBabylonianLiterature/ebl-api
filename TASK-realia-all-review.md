# TASK-realia-all — Review of PR #735 (`add-realia-slugs-endpoint`)

## Summary

Adds `GET /realia/all`, returning the sorted `_id` of every Realia entry that is
not a redirect stub. Backed by a new repository method and a Mongo `$expr`
filter, covered by repository- and route-level tests.

The feature works and the exclusion rule is correct on live data (verified: 21
stubs excluded out of 24,361 documents, exact parity with an independent Python
implementation of the domain rule). Issues found were naming honesty, a test that
could not fail, an unexplained load-bearing constant, and committed task
artifacts. All are addressed in this branch.

## Findings

### 1. Task-tracking artifacts committed to the branch — Severity: Blocker

`TASK-realia-all-log.md` and `TASK-realia-all-todo.md` were present at `HEAD`.
Commits `e4a879f8` and `27726a7a` each removed them, but the final commit
`ca7b8d3c` re-added both. Project instructions require these to be gone before
merge.

**Reproduction:** `git show --stat ca7b8d3c` lists both files as added.

**Recommendation / applied:** `git rm` both files.

### 2. `list_all_realia() -> Sequence[str]` is misleading — Severity: Medium

Raised by Sourcery, and the problem is deeper than reported. The name is wrong
twice:

- it returns **IDs**, not `RealiaEntry` objects, unlike `search()`;
- it does not return **all** realia — it deliberately omits 21 redirect stubs.

Sourcery's suggested fix (return `Sequence[RealiaEntry]` and project to IDs in
the web layer) is **rejected**: it would load 24k full documents and run
bibliography injection over all of them purely to throw everything away but the
`_id`. The rename option is the right one.

**Recommendation / applied:** renamed to `list_non_redirect_ids()`. Note "ids",
not "realia_ids" — `realiaId` is a *different* field from `_id` in this schema
(`find_by_realia_id` queries it), so "realia id" would actively mislead.

### 3. Route test cannot detect broken sorting — Severity: Medium

Raised by Sourcery. `test_list_all_realia` seeded
`identifiers = ["Anu", "Enlil, Ellil", "Pig"]` — already in sorted order — then
asserted `result.json == identifiers`. Insertion order equals sorted order, so
the assertion passes even if sorting is removed entirely.

**Reproduction:** delete `sorted(...)` from the repository method; the route test
still passes.

**Recommendation / applied:** seed in unsorted order (`"Pig"`, `"Anu"`,
`"Enlil, Ellil"`) and assert the sorted result. The test now fails if sorting
regresses. (The repository-level test already did this correctly.)

### 4. `reallexikon > 1` is an unexplained load-bearing constant — Severity: Medium

`_has_own_content_expression` treated *two or more* reallexikon entries as own
content, but not one. The asymmetry reads as arbitrary and is the single
condition the whole feature depends on.

**Reproduction:** every one of the 21 stubs has **exactly one** reallexikon entry
with an unresolvable reference. Relax the threshold from `> 1` to `> 0` and the
filter excludes **zero** documents — the endpoint silently degrades to "list
everything" with no test failure at the repository level on real data.

**Recommendation / applied:** named the thresholds
(`PLACEHOLDER_REALLEXIKON_COUNT`, `REDIRECT_CROSS_REFERENCE_COUNT`) and
restructured the filter to state the rule directly — *a redirect stub is an entry
whose only content is a single cross-reference* — instead of its De Morgan dual.
Behaviour is unchanged (see Verification).

### 5. `/realia/all` shadows an entry named `all` — Severity: Low (accepted)

Falcon matches the static `/realia/all` route ahead of `/realia/{realia_id}`, so
an entry literally named `all` becomes unreachable at that path. Confirmed **no
such entry exists** in the live collection, and the branch already locks the
behaviour in `test_list_non_redirect_ids_shadows_entry_named_all`.

**Recommendation:** accepted as-is. Flagged only so the trade-off is a decision
rather than an accident. Entries whose IDs contain `/` (2,609 of them) are
unaffected — they are served by the existing `RealiaLemmaSink`.

### 6. Endpoint named `all` returns a filtered list — Severity: Low (not changed)

The URL says `all` while the response deliberately omits 21 entries. This is a
frontend-facing contract, so it is **not** changed here; noted for the API owner.

## Verification

- Three-way parity over the full live collection (24,361 docs): the pre-refactor
  `$expr`, the refactored `$expr`, and an independent Python implementation of
  the domain rule all include the **same 24,340 IDs** and exclude the **same 21
  stubs**. Zero disagreements in either direction.
- `task format` — clean (729 files).
- `task test` — 3790 passed, 2 skipped, 1 xfailed.
- Coverage on all changed modules — **100%** (`realia_repository.py`,
  `mongo_realia_repository.py`, `web/realia.py`).
- `flake8 --max-line-length=120` — clean.
- `mypy --ignore-missing-imports` — zero errors in the changed modules. (51
  errors remain elsewhere in `corpus`/`ebl_ai_client`, pulled in via transitive
  imports; identical count on the base commit, untouched by this PR.)
- File-length gate — all changed files under 250 lines (max: 246).

## Recommendation

**Approve after the applied fixes.** The exclusion rule is empirically correct
and now states its own intent; the sorting test can now fail; the task artifacts
are gone. Findings 5 and 6 are contract observations for the API owner, not
merge blockers.

> Remove this review file before the PR is merged.
