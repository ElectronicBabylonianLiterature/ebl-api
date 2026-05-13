# TASK-1 — Realia Collection: Work Log

## 2026-05-13

### Context gathered
- Read Trello card JSON (`realia_trello_card.json`). Final schema (latest revision) has:
  - `_id`, `relatedTerms[]`, `type[]` (entityType), `afoRegister[]`, `references[]` (referenceObject), `wikidataId[]`, `reallexikon[]`
- Read existing module patterns: `dictionary/`, `afo_register/`, `dossiers/`, `provenance/`
- `NamedEntityType` enum already exists in `fragmentarium/domain/named_entity.py` — likely reusable as `type`
- `AkkadischeGlossareUndIndicesSchema` in `dictionary/application/word_schema.py` is the near-identical pattern for `afoRegister` entries (needs `crossReference` added)
- `ApiReferenceSchema` in `bibliography/application/reference_schema.py` handles `referenceObject`
- `query_collation.py` already handles character normalisation (collation H covers `ʾ`); a `REALIA` entry needs adding
- App bootstrap pattern: `context.py` + `app.py` + `web/bootstrap.py`

### Status
- Scope defined; all 5 clarification questions answered
- TASK-1-todo.md updated: `RealiaType` separate enum, read-only routes, Realia-specific char-strip pre-processing, no create/ingest endpoint, `afoRegister[].reference` confirmed as plain string
- Ready for implementation

## 2026-05-13 (implementation)

### Files created
- `ebl/realia/__init__.py` and sub-package `__init__.py` files (5 files)
- `ebl/realia/domain/realia_entry.py` — domain model (`RealiaType`, `AfoRegisterEntry`, `ReallexikonEntry`, `RealiaEntry`)
- `ebl/realia/application/realia_repository.py` — abstract `RealiaRepository` ABC
- `ebl/realia/infrastructure/mongo_realia_repository.py` — Marshmallow schemas + `MongoRealiaRepository` (find + search with bibliography injection)
- `ebl/realia/web/realia.py` — `RealiaResource` (`GET /realia/{id}`) and `RealiaSearchResource` (`GET /realia?query=...`)
- `ebl/realia/web/bootstrap.py` — `create_realia_routes(api, context)`
- `ebl/tests/factories/realia.py` — `AfoRegisterEntryFactory`, `ReallexikonEntryFactory`, `RealiaEntryFactory`
- `ebl/tests/realia/__init__.py`
- `ebl/tests/realia/test_realia_entry.py` — 7 tests (defaults, creation, schema round-trips)
- `ebl/tests/realia/test_realia_repository.py` — 6 tests (find, not-found, search by id/term/strip/empty/no-match)
- `ebl/tests/realia/test_realia_route.py` — 5 tests (GET by id, 404, search, empty, no-match)

### Files modified
- `ebl/common/query/query_collation.py` — added `"realia"` to `DataType`, `REALIA` to `Fields`, `strip_realia_query_chars()` helper
- `ebl/context.py` — added `realia_repository: RealiaRepository` field
- `ebl/app.py` — wired `MongoRealiaRepository` and `create_realia_routes`
- `ebl/tests/conftest.py` — added `realia_repository` fixture; wired into `context` fixture

### Test results
- `pytest ebl/tests/realia/` → **18 passed** ✅
- `pytest ebl/tests/common/` → **24 passed** (collation unchanged) ✅
- `pytest ebl/tests/test_app_bootstrap.py` → **2 passed** ✅

### Status: UNDER REVIEW — PR #715 open; TASK-1-review.md written; 4 actionable findings require fixes before merge

## 2026-05-13 (review)

### Review completed
- Fetched Sourcery + qlty automated reviews from GitHub
- Audited all 22 changed files locally
- Ran 18 realia tests (all pass), coverage (98%), flake8 (clean), mypy
- Identified 8 findings; 2 are must-fix before merge (F1 HIGH, F2 MEDIUM)
- TASK-1-review.md created
