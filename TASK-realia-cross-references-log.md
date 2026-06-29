# TASK-realia-cross-references — Work Log

## 2026-06-29

- Audited every side of the Realia module: domain model, marshmallow schemas
  (all `unknown = EXCLUDE`), the Mongo repository, routes/bootstrap, tests,
  and factories. Confirmed `/realia/{id}` matched the mutable lemma `_id` and
  that no OpenAPI/swagger fixtures exist for Realia.
- Implemented the feature:
  - `domain/realia_entry.py`: added `CrossReference`, `AfoCrossReference`,
    and the new fields on `RealiaEntry` / `AfoRegisterEntry`.
  - schemas: added `CrossReferenceSchema`, `AfoCrossReferenceSchema`, and new
    fields on `AfoRegisterEntrySchema` / `RealiaEntrySchema` with validation.
  - repository: added `find_by_realia_id` (queries `{"realiaId": ...}`) with a
    shared `_load_entry` helper; added the abstract method.
  - web: added `RealiaByIdResource` and the `/realia/by-id/{realia_id}` route.
  - factories: added the new fields and cross-reference factories.
- Verified Falcon 3.1.3 prefers the literal `by-id` segment over the
  `{realia_id}` field template, so the lemma route is not shadowed.
- Review pass against the Copilot instructions found the 250-line hard gate
  was breached by three files. Refactored:
  - extracted all marshmallow schemas into
    `infrastructure/realia_schemas.py` (repository now imports them);
  - split `test_realia_entry.py` → `test_realia_cross_references.py`;
  - split `test_realia_repository.py` → `test_realia_repository_search.py`;
  - moved shared seeding helpers into
    `tests/realia/realia_repository_helpers.py` and reused them in the route
    test (removed duplicated `_seed_entry` body).
- Gates: `black` clean; `ruff` clean; `flake8 --max-line-length=120` clean;
  `mypy` (changed files) and `pyre` clean; full suite 3752 passed / 2 skipped
  / 1 xfailed; 100% coverage on all changed source modules.
- Wrote `TASK-realia-cross-references-review.md` with Summary, Findings,
  Severity, Reproduction Steps, Recommendation.
- Whole-PR review (branch vs master): ran two independent review passes plus a
  manual read of the shared files. Applied the AfoCrossReference required-field
  fix and added a regex-injection search test.
- Follow-up pass — addressed every remaining review finding:
  - Added `MongoRealiaRepository.create_indexes()` with a partial unique index
    on `realiaId` (`partialFilterExpression={"realiaId": {"$gt": ""}}`), the
    abstract method, and the bootstrap call. Tests cover declaration,
    duplicate rejection, and blank/missing tolerance.
  - Simplified bibliography injection to use `Reference.set_document` + a
    shared `_document_for` helper (drops the `ApiReferenceSchema` round-trip).
  - Guarded `_rank` against non-list `relatedTerms`.
  - Fixed the `Unexepcted` typo in `scopes.py` and its test.
  - Added tests: lemma named `by-id` not shadowed, whitespace-only query,
    diacritic tiebreak, multi-element reallexikon richness, non-list terms.
  - Documented the lean reallexikon reference and the `_id` response key as
    deliberate design decisions.
- Gates re-run: `black`/`ruff`/`flake8 --max-line-length=120` clean, `mypy`
  (changed files) + `pyre` clean, full suite 3761 passed / 0 failed, 100%
  coverage on every changed source module, all files < 250 lines,
  `markdownlint` clean.
