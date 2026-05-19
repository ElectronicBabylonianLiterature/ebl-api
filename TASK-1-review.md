# TASK-1 — PR #715 Review: Add Realia Module

**Branch:** `add-realia` → `master`
**PR:** https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/715
**Reviewed:** 2026-05-13
**Reviewer:** GitHub Copilot

---

## Summary

Introduces a new read-only Realia module: domain model, MongoDB repository with bibliography injection, Falcon HTTP endpoints (`GET /realia/{id}` and `GET /realia?query=...`), collation support, and 18 tests. +771 / −1 lines across 22 files.

Automated reviews: **Sourcery** (3 inline suggestions, 3 overall comments) and **qlty** (1 function-parameter count comment). All findings documented below.

---

## Findings

### F1 — Bug: `find()` returns un-injected entry (bibliography not populated)

**Severity:** HIGH

**File:** `ebl/realia/infrastructure/mongo_realia_repository.py`, lines 97–100

**Description:**
`_inject_bibliography()` mutates the list it receives in-place by replacing list slots (`entries[index] = self._inject_entry(...)`). In `find()`, a temporary list `[entry]` is created and passed to the method; that list slot is updated but the local variable `entry` still points to the original, un-injected object. The returned entry has all `references[].document` and `reallexikon[].reference.document` values as `None`.

By contrast, `search()` correctly returns the list (whose slots have been updated) so bibliography injection works there.

**Reproduction Steps:**
1. Insert a realia entry with bibliography references via the repository.
2. Call `repository.find(entry.id)`.
3. Inspect `result.references[0].document` — it will be `None`.

**Recommendation:**
```python
def find(self, realia_id: str) -> RealiaEntry:
    document = self._realia_collection.find_one_by_id(realia_id)
    entries = [RealiaEntrySchema().load(document)]
    self._inject_bibliography(entries)
    return entries[0]
```
Also remove the now-redundant `if document is None:` guard (see F2).

---

### F2 — Dead Code: `if document is None` guard in `find()` is unreachable

**Severity:** MEDIUM

**File:** `ebl/realia/infrastructure/mongo_realia_repository.py`, lines 93–95

**Description:**
`MongoCollection.find_one_by_id()` delegates to `find_one()`, which raises `NotFoundError` internally when the document is not found. It never returns `None`. The guard and custom error message at lines 94–95 are therefore unreachable dead code — and also explain why line 95 shows as uncovered in the coverage report.

**Side effect:** The custom message `"Realia entry '{id}' not found."` is never raised from the repository; MongoDB's generic query-based message is raised instead. The web resource compensates by re-wrapping the error (see F3), but the logic should live in the repository's `find()`.

**Recommendation:**
Remove the `if document is None:` guard. To preserve the user-friendly message, use a try/except in `find()`:
```python
def find(self, realia_id: str) -> RealiaEntry:
    try:
        document = self._realia_collection.find_one_by_id(realia_id)
    except NotFoundError:
        raise NotFoundError(f"Realia entry '{realia_id}' not found.")
    entries = [RealiaEntrySchema().load(document)]
    self._inject_bibliography(entries)
    return entries[0]
```

---

### F3 — Redundant Exception Wrapping in `RealiaResource.on_get`

**Severity:** LOW-MEDIUM
**Source:** Sourcery review

**File:** `ebl/realia/web/realia.py`, lines 13–15

**Description:**
`on_get` catches `NotFoundError` from the repository and immediately re-raises a new `NotFoundError` with the same message, discarding the original exception context. If the repository message is standardised (per F2 recommendation), this catch block serves no purpose and should be removed.

**Recommendation:**
Once F2 is resolved with a consistent message in the repository, simplify to:
```python
def on_get(self, _req: Request, resp: Response, realia_id: str) -> None:
    entry = self._realia_repository.find(realia_id)
    resp.media = RealiaEntrySchema().dump(entry)
```
Falcon's error handler will propagate `NotFoundError` as a 404 response.

---

### F4 — Non-deterministic Search Result Ordering

**Severity:** LOW-MEDIUM
**Source:** Sourcery review

**File:** `ebl/realia/infrastructure/mongo_realia_repository.py`, line 126

**Description:**
`find_many(mongo_query).limit(MAX_SEARCH_RESULTS)` does not include a `.sort(...)`. MongoDB's natural order depends on storage and index internals; the returned subset may change unpredictably over time, especially after document updates or collection rebuilds.

**Recommendation:**
```python
cursor = (
    self._realia_collection
    .find_many(mongo_query)
    .sort("_id")
    .limit(MAX_SEARCH_RESULTS)
)
```

---

### F5 — Coverage Gaps

**Severity:** LOW

**Files:** multiple

**Description:**
Coverage report: `mongo_realia_repository.py` at 98% — lines 95 and 192 uncovered.

| Line | Code | Reason |
|------|------|--------|
| 95 | `raise NotFoundError(...)` in `find()` | Dead code (see F2) |
| 192 | `else: result.append(rlex)` in `_inject_reallexikon()` | `ReallexikonEntryFactory` always builds a `reference`; the `None` branch is never exercised |

Also noted by Sourcery:
- `test_find_existing_entry` does not assert that `references[].document` is populated after `find()` — would have caught F1.
- No route test for omitting the `query` param entirely (vs. empty string `""`); `RealiaSearchResource.on_get` defaults to `""` via `req.get_param("query", default="")`.

**Recommendation:**
1. Fix F1 and F2; line 95 coverage will then be achievable with `test_find_not_found`.
2. Add a `ReallexikonEntryFactory` build that sets `reference=None` and use it in a test path through `_inject_reallexikon`.
3. Add bibliography-injection assertions to `test_find_existing_entry`.
4. Add `test_search_realia_missing_query` to `test_realia_route.py`.

---

### F6 — Weak Generic Type Annotation in `_collect_reference_ids`

**Severity:** LOW

**File:** `ebl/realia/infrastructure/mongo_realia_repository.py`, line 131

**Description:**
`ids: set = set()` uses the unparameterised `set`. Should be `ids: Set[BibliographyId]` (or `set[BibliographyId]` in Python 3.9+) for consistency with project type-hint standards.

**Recommendation:**
```python
ids: set[BibliographyId] = set()
```

---

### F7 — Pre-existing Mypy Errors Also Present in PR

**Severity:** INFO (pre-existing, not introduced by this PR)

**File:** `ebl/common/query/query_collation.py`, lines 41–47

**Description:**
mypy reports `Incompatible return value type (got "dict[str, list[str]]", expected "dict[str, Sequence[str]]")` for all four `return Fields.<X>.value` statements in `findByDataType`. The three pre-existing returns (DICTIONARY, AFO_REGISTER, COLOPHONS) had this error on master; the PR's REALIA return adds a fourth with the same pattern.

**Recommendation:**
Fixing is out of scope for this PR but worth a follow-up: change the return type annotation of `findByDataType` to `Mapping[str, Sequence[str]]`.

---

### F8 — qlty: `context` Fixture Has 23 Parameters

**Severity:** INFO (pre-existing pattern, flagged by qlty bot)
**Source:** qlty review comment `qlty:function-parameters` — https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/715#discussion_r3235064120

**File:** `ebl/tests/conftest.py`, line 518

**Description:**
qlty flagged the `context` fixture for exceeding its function-parameter threshold (count = 23). The PR added `realia_repository` as the 23rd argument. Full signature:

```python
@pytest.fixture
def context(
    ebl_ai_client,
    cropped_sign_images_repository,
    word_repository,
    sign_repository,
    file_repository,
    photo_repository,
    folio_repository,
    thumbnail_repository,
    fragment_repository,
    text_repository,
    changelog,
    bibliography_repository,
    provenance_repository,
    seeded_provenance_service,
    annotations_repository,
    lemma_repository,
    afo_register_repository,
    dossiers_repository,
    findspot_repository,
    realia_repository,       # ← added by this PR
    user,
    parallel_line_injector,
    mongo_cache_repository,
) -> ebl.context.Context:
```

This matches the existing convention: every new module adds its repository fixture to the single shared `context` fixture. The warning is consistent with all prior module additions.

**Recommendation:**
No immediate action required; accepted codebase pattern. A future refactor could split the `context` fixture into domain-specific groups, but that is out of scope for this PR.

---

## Task File Reminder

Before merging, the following files must be removed from the repository:
- `TASK-1-todo.md`
- `TASK-1-log.md`
- `TASK-1-review.md`
- `TASK-1-realia_trello_card.json`

---

## Verdict

| # | Severity | Status |
|---|----------|--------|
| F1 — `find()` returns un-injected entry | **HIGH** | ✅ Fixed |
| F2 — Dead code guard in `find()` | MEDIUM | ✅ Fixed |
| F3 — Redundant exception wrapping | LOW-MEDIUM | ✅ Fixed |
| F4 — Missing sort on search results | LOW-MEDIUM | ✅ Fixed |
| F5 — Coverage gaps | LOW | ✅ Fixed |
| F6 — Weak generic type annotation | LOW | ✅ Fixed |
| F7 — Pre-existing mypy errors | INFO | Out of scope |
| F8 — Fixture parameter count | INFO | Accepted pattern |
