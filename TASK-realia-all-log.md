# TASK-realia-all — Work Log

## Round 1 — fix: reallexikon reference null-check

### Problem found via live verification

Ran the committed rule against the live `ebldev` collection (24,361 docs) and
compared its included set against the domain/frontend rule:

- domain rule → excluded 21 stubs
- committed `$expr` → excluded **0** (included everything)

Root cause: `reallexikon.reference` is stored in three shapes —
`dict_with_id` (9222), `dict_without_id` (510), and null. The frontend/domain
deserializer (`ReallexikonReferenceField._from_id`) treats a reference **dict
without an `id`** (and an empty string) as **null**, but the committed Mongo
check `reference != null` counted those 510 dicts as real references. Each of
the 21 true stubs owns such a dict, so the rule saw "own content" and kept them.

### Fix

The reallexikon reference count now counts a reference as resolvable only when
it matches the domain rule, via `_is_resolvable_reference`:

- string → non-empty, or
- object → has a non-empty `id`,
- otherwise not a reference.

### Verification

Re-ran the same diff over all 24,361 live docs:

- domain rule → 24,340 included / 21 excluded
- fixed `$expr` → 24,340 included
- disagreements: **0 kept-stubs, 0 dropped-real** (exact parity both directions)

## Round 2 — PR #735 review

Full review in `TASK-realia-all-review.md`. Four issues fixed.

### 1. Task artifacts were committed (blocker)

`TASK-realia-all-log.md` and `TASK-realia-all-todo.md` were present at `HEAD`:
commits `e4a879f8` and `27726a7a` each removed them, but `ca7b8d3c` re-added
both. They are removed again in the follow-up commit.

### 2. `list_all_realia` renamed to `list_non_redirect_ids` (Sourcery)

The old name was wrong twice: it returned **ids**, not `RealiaEntry` objects,
and it did not return **all** realia — it omits 21 redirect stubs by design.
Sourcery's alternative (return `Sequence[RealiaEntry]`, project in the web
layer) was rejected: it would load 24k full documents and run bibliography
injection over all of them purely to keep `_id`.

Named "ids", not "realia_ids", on purpose: `realiaId` is a **different field**
from `_id` in this schema (`find_by_realia_id` queries it), so "realia id" would
actively mislead.

### 3. Route test could not fail (Sourcery)

`test_list_all_realia` seeded `["Anu", "Enlil, Ellil", "Pig"]` — already in
sorted order — then asserted `result.json == identifiers`. Insertion order
equalled sorted order, so the test passed even with `sorted(...)` deleted from
the repository. It now seeds unsorted (`"Pig"`, `"Anu"`, `"Enlil, Ellil"`) and
asserts the sorted result.

### 4. `reallexikon > 1` was an unexplained load-bearing constant

Every one of the 21 stubs has **exactly one** reallexikon entry with an
unresolvable reference. Relaxing the threshold from `> 1` to `> 0` makes the
filter exclude **zero** documents — the endpoint silently degrades to "list
everything", with no repository-level test failure on real data.

Fixed by naming the thresholds (`REDIRECT_CROSS_REFERENCE_COUNT`,
`PLACEHOLDER_REALLEXIKON_COUNT`) and restructuring the filter to state the rule
directly — *a redirect stub is an entry whose only content is a single
cross-reference* — instead of its De Morgan dual.

### Hypothesis checked and rejected

The filter ignores `wikidataId`, `type`, `relatedTerms` and `realiaId`, so an
entry carrying only those plus one cross-reference would be dropped. Checked
against live data: all 21 stubs carry `type` and `realiaId` (13 also carry
`relatedTerms`) and none carry a `wikidataId`. Those fields are metadata every
document has, not article content. The rule is correct as written.

### Verification of the `$expr` refactor

Three-way parity over the full live collection (24,361 docs): the pre-refactor
`$expr`, the refactored `$expr`, and an independent Python implementation of the
domain rule all include the **same 24,340 ids** and exclude the **same 21
stubs**. Zero disagreements in either direction.

## Gates

- `task format` — clean (729 files)
- `task test` — 3790 passed, 2 skipped, 1 xfailed
- Coverage on changed modules — **100%** (`realia_repository.py`,
  `mongo_realia_repository.py`, `web/realia.py`)
- `flake8 --max-line-length=120` — clean
- `mypy --ignore-missing-imports` — zero errors in changed modules (51 remain in
  `corpus`/`ebl_ai_client` via transitive imports; identical count on the base
  commit, untouched by this PR)
- `task lint-md` — clean
- File-length gate — all changed files under 250 lines (max: 246)

> Remove this file (and `TASK-realia-all-todo.md`, `TASK-realia-all-review.md`)
> before the PR is merged.
