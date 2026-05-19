# TASK-1 — Realia Collection: API Work Scope & Implementation

## Status: COMPLETE ✅ (all 18 tests passing)

---

## Decisions (Clarifications Resolved)

| # | Question | Decision |
|---|---|---|
| 1 | `type` enum | **Separate `RealiaType` enum** — allows future divergence from `NamedEntityType`; can be unified later |
| 2 | `afoRegister[].reference` | **Plain string** — simple citation/note, not a full `referenceObject` |
| 3 | Write endpoints | **Read-only (GET) only** for this phase |
| 4 | Character-strip for search | **Realia-specific pre-processing step** applied before existing collation, scoped to `REALIA` data type |
| 5 | Admin ingest endpoint | **Not needed** — data loaded directly into MongoDB |

---

## Scope

### 1. New module `ebl/realia/`

#### 1a. Domain — `ebl/realia/domain/realia_entry.py`
- [x] `RealiaType` enum (separate from `NamedEntityType`; mirror its structure for future compatibility)
- [x] `AfoRegisterEntry` attrs class: `main_word`, `note`, `afo`, `reference` (str), `cross_reference`
- [x] `ReallexikonEntry` attrs class: `id`, `title`, `reference` (full `Reference` object), `content`
- [x] `RealiaEntry` attrs class: `id`, `related_terms`, `type` (list of `RealiaType`), `afo_register`, `references`, `wikidata_id`, `reallexikon`

#### 1b. Application — `ebl/realia/application/realia_repository.py`
- [x] Abstract `RealiaRepository` interface: `find(realia_id)`, `search(query)`

#### 1c. Infrastructure — `ebl/realia/infrastructure/mongo_realia_repository.py`
- [x] `AfoRegisterEntrySchema` (Marshmallow) — mirrors `AkkadischeGlossareUndIndicesSchema` + `crossReference`; `reference` field stays plain string
- [x] `ReallexikonEntrySchema` (Marshmallow) — `id`, `title`, `reference` via `ApiReferenceSchema`, `content`
- [x] `RealiaEntrySchema` (Marshmallow) — full document schema
- [x] `MongoRealiaRepository` — implements `find` and `search` against `realia` collection
- [x] Search pipeline: match on `_id` + `relatedTerms` with existing collation; **Realia-only pre-processing** strips `""„ʾ''` from query before collation is applied

#### 1d. Web — `ebl/realia/web/realia.py`
- [x] `RealiaResource` — `GET /realia/{realia_id}` (fetch single entry by id)
- [x] `RealiaSearchResource` — `GET /realia?query=...` (search by `_id` + `relatedTerms`)

#### 1e. Web — `ebl/realia/web/bootstrap.py`
- [x] `create_realia_routes(api, context)` registering both routes

### 2. Collation (`ebl/common/query/query_collation.py`)
- [x] Add `"realia"` to `DataType` literal
- [x] Add `REALIA` to `Fields` enum with `COLLATED_FIELDS: ["_id", "relatedTerms"]`
- [x] Add `strip_realia_query_chars(query: str) -> str` helper that removes `""„ʾ''` before collation

### 3. App wiring
- [x] `ebl/context.py`: add `realia_repository: RealiaRepository`
- [x] `ebl/app.py`: add `MongoRealiaRepository(database)` to `create_context()` and `create_realia_routes(api, context)` to `create_app()`

### 4. Tests
- [x] `ebl/tests/realia/__init__.py`
- [x] `ebl/tests/realia/test_realia_entry.py` — domain model + schema round-trip
- [x] `ebl/tests/realia/test_realia_repository.py` — integration tests (`find` + `search`, read-only)
- [x] `ebl/tests/realia/test_realia_route.py` — Falcon resource route tests
- [x] Factory `ebl/tests/factories/realia.py` — `RealiaEntryFactory`

---

## Files Created / Modified (planned)

| Action | Path |
|--------|------|
| CREATE | `ebl/realia/__init__.py` |
| CREATE | `ebl/realia/domain/realia_entry.py` |
| CREATE | `ebl/realia/application/realia_repository.py` |
| CREATE | `ebl/realia/infrastructure/mongo_realia_repository.py` |
| CREATE | `ebl/realia/web/realia.py` |
| CREATE | `ebl/realia/web/bootstrap.py` |
| MODIFY | `ebl/common/query/query_collation.py` |
| MODIFY | `ebl/context.py` |
| MODIFY | `ebl/app.py` |
| CREATE | `ebl/tests/realia/__init__.py` |
| CREATE | `ebl/tests/realia/test_realia_entry.py` |
| CREATE | `ebl/tests/realia/test_realia_repository.py` |
| CREATE | `ebl/tests/realia/test_realia_route.py` |
| CREATE | `ebl/tests/factories/realia.py` |
