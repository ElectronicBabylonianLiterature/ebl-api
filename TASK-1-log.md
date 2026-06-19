# TASK-1 — Realia Collection: Work Log

## 2026-05-13

### Context gathered

- Read Trello card JSON (`realia_trello_card.json`). Final schema (latest
  revision) has:
  - `_id`, `relatedTerms[]`, `type[]` (entityType), `afoRegister[]`,
    `references[]` (referenceObject), `wikidataId[]`, `reallexikon[]`
- Read existing module patterns: `dictionary/`, `afo_register/`, `dossiers/`,
  `provenance/`
- `NamedEntityType` enum already exists in
  `fragmentarium/domain/named_entity.py` — likely reusable as `type`
- `AkkadischeGlossareUndIndicesSchema` in
  `dictionary/application/word_schema.py` is the near-identical pattern for
  `afoRegister` entries (needs `crossReference` added)
- `ApiReferenceSchema` in `bibliography/application/reference_schema.py` handles
  `referenceObject`
- `query_collation.py` already handles character normalisation (collation H
  covers `ʾ`); a `REALIA` entry needs adding
- App bootstrap pattern: `context.py` + `app.py` + `web/bootstrap.py`

### Status

- Scope defined; all 5 clarification questions answered
- TASK-1-todo.md updated: `RealiaType` separate enum, read-only routes,
  Realia-specific char-strip pre-processing, no create/ingest endpoint,
  `afoRegister[].reference` confirmed as plain string
- Ready for implementation

## 2026-05-13 (implementation)

### Files created

- `ebl/realia/__init__.py` and sub-package `__init__.py` files (5 files)
- `ebl/realia/domain/realia_entry.py` — domain model (`RealiaType`,
  `AfoRegisterEntry`, `ReallexikonEntry`, `RealiaEntry`)
- `ebl/realia/application/realia_repository.py` — abstract `RealiaRepository` ABC
- `ebl/realia/infrastructure/mongo_realia_repository.py` — Marshmallow schemas +
  `MongoRealiaRepository` (find + search with bibliography injection)
- `ebl/realia/web/realia.py` — `RealiaResource` (`GET /realia/{id}`) and
  `RealiaSearchResource` (`GET /realia?query=...`)
- `ebl/realia/web/bootstrap.py` — `create_realia_routes(api, context)`
- `ebl/tests/factories/realia.py` — `AfoRegisterEntryFactory`,
  `ReallexikonEntryFactory`, `RealiaEntryFactory`
- `ebl/tests/realia/__init__.py`
- `ebl/tests/realia/test_realia_entry.py` — 7 tests (defaults, creation, schema
  round-trips)
- `ebl/tests/realia/test_realia_repository.py` — 6 tests (find, not-found,
  search by id/term/strip/empty/no-match)
- `ebl/tests/realia/test_realia_route.py` — 5 tests (GET by id, 404, search,
  empty, no-match)

### Files modified

- `ebl/common/query/query_collation.py` — added `"realia"` to `DataType`,
  `REALIA` to `Fields`, `strip_realia_query_chars()` helper
- `ebl/context.py` — added `realia_repository: RealiaRepository` field
- `ebl/app.py` — wired `MongoRealiaRepository` and `create_realia_routes`
- `ebl/tests/conftest.py` — added `realia_repository` fixture; wired into
  `context` fixture

### Test results

- `pytest ebl/tests/realia/` → **18 passed** ✅
- `pytest ebl/tests/common/` → **24 passed** (collation unchanged) ✅
- `pytest ebl/tests/test_app_bootstrap.py` → **2 passed** ✅

### Status: UNDER REVIEW — PR #715 open; review written; 4 findings to fix

## 2026-05-13 (review)

### Review completed

- Fetched Sourcery + qlty automated reviews from GitHub
- Audited all 22 changed files locally
- Ran 18 realia tests (all pass), coverage (98%), flake8 (clean), mypy
- Identified 8 findings; 2 are must-fix before merge (F1 HIGH, F2 MEDIUM)
- TASK-1-review.md created

## 2026-05-13 (review findings addressed)

### Changes made to address findings

- **F1+F2** `mongo_realia_repository.py` `find()`: removed dead `if document is
  None:` guard; fixed bibliography injection by using `entries[0]`; standardised
  error message with try/except around `find_one_by_id`
- **F3** `web/realia.py` `on_get`: removed redundant `NotFoundError` re-wrap;
  removed unused `NotFoundError` import
- **F4** `mongo_realia_repository.py` `search()`: added `.sort("_id")` before
  `.limit(MAX_SEARCH_RESULTS)`
- **F5a** `test_realia_repository.py`: added bibliography injection assertions
  to `test_find_existing_entry`; added
  `test_search_entry_with_reallexikon_no_reference` to cover `None`-reference
  branch in `_inject_reallexikon`
- **F5b** `test_realia_route.py`: added `test_search_realia_missing_query`
- **F6** `mongo_realia_repository.py`: fixed `ids: set` → `ids:
  set[BibliographyId]`

### Test results after fixes

- `pytest ebl/tests/realia/` → **20 passed** ✅ (2 new tests added)
- `pytest ebl/tests/common/ ebl/tests/test_app_bootstrap.py` → **26 passed** ✅
- Coverage `ebl/realia/` → **100%** ✅ (was 98%)

### Status: FIXES APPLIED — awaiting user approval to commit/push

## 2026-05-13 (post-commit refactor & gate fixes)

### Changes made after initial commit

- **`_inject_bibliography` refactored**: split into `_inject_entry`,
  `_inject_references`, `_inject_reallexikon` — each with a single
  responsibility
- **Pyre type errors fixed**: helper method signatures updated to
  `Sequence[Reference]` / `Sequence[ReallexikonEntry]` / `Tuple[..., ...]`; test
  fixtures using `_realia_collection` typed as `MongoRealiaRepository` instead
  of abstract `RealiaRepository`
- **Lint errors fixed**: removed unused imports (`re`, `RealiaType`,
  `BibliographyEntryFactory`, `pytest`, `NotFoundError`, `RealiaRepository`)
  from infrastructure and test files
- **Committed**: `4b08062b` — "refactor: split _inject_bibliography into focused
  helpers; fix lint and type errors"

### Gate results (all pass)

- `task format` ✅
- `task lint` ✅
- `task type` ✅
- `pytest ebl/tests/realia/` → 18 passed ✅

## 2026-06-02 (dev database seed)

### Seed data

- Created `realia-seed-pig.json` — "Pig" entry based on UI screenshot, matching
  the `RealiaEntrySchema` wire format:
  - `_id`: "Pig", `relatedTerms`: ["Schwein", "Schweinefett"], `wikidataId`:
    ["Q787"]
  - 3 reallexikon entries (Schwein A/B/C with RlA article IDs and titles)
  - 2 afoRegister entries (AfO 52 (2018) 645)
  - 1 reference: De Zorzi 2016 (DISCUSSION type)
- Upserted into dev `realia` collection — confirmed `upserted_id='Pig'`
- File saved for later reuse: `realia-seed-pig.json`
