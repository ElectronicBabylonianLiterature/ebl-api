# TODO: Implement Proper Noun Creation Endpoint (Backend)

## Overview

Implement a `POST /words/create-proper-noun` backend endpoint that persists newly created proper nouns to the Word collection in MongoDB. This endpoint will accept a lemma and optional POS tags array, validate inputs, and create a complete Word document following the established database schema.

The implementation spans three layers:

1. **Repository Layer**: Database abstraction for Word creation
2. **Service Layer**: Business logic delegation
3. **Web Layer**: HTTP endpoint and request validation

## Authorization

**Scope Required:** `create:proper_nouns`

This endpoint is protected and only accessible to users with the `create:proper_nouns` scope in their Auth0 token. Users without this scope will receive a **403 Forbidden** response.

The scope is defined in Auth0 as part of the ebl-api API permissions (see [Scopes section in README.md](README.md#scopes)).

## Reference Example

Proper noun document structure (from database):

```json
{
 "_id": "Marduk I",
 "lemma": ["Marduk"],
 "homonym": "I",
 "pos": ["DN"],
 "attested": true,
 "meaning": "",
 "legacyLemma": "Marduk",
 "guideWord": "Marduk",
 "arabicGuideWord": "",
 "origin": ["EBL"],
 "forms": [],
 "logograms": [],
 "derived": [],
 "derivedFrom": null,
 "amplifiedMeanings": [],
 "oraccWords": [],
 "roots": []
}
```

## Implementation Phases

### Phase 1: Schemas & Data Validation

- [x] Add `ProperNounCreationRequestSchema` in [ebl/dictionary/application/word_schema.py](ebl/dictionary/application/word_schema.py)
  - [x] Define `lemma` field: Required string, non-empty validation
  - [x] Define `pos` field: Optional list of strings, default to []
  - [x] Validate invalid types (non-string, empty list entries)
  - [x] Ensure empty or missing `pos` returns []
  - [x] Ensure empty `lemma` fails validation
- [x] Add schema tests in [ebl/tests/dictionary/test_create_proper_noun.py](ebl/tests/dictionary/test_create_proper_noun.py)
  - [x] Valid request with lemma only
  - [x] Valid request with lemma and pos list
  - [x] Invalid when lemma is missing
  - [x] Invalid when lemma is empty
  - [x] Invalid when pos is not a list
  - [x] Invalid when pos contains non-string values
  - [x] Default pos to [] when omitted

### Phase 2: Repository Layer

- [x] Extend `WordRepository` interface in [ebl/dictionary/application/word_repository.py](ebl/dictionary/application/word_repository.py)
  - [x] Add `create_proper_noun(self, lemma: str, pos_tags: list[str]) -> WordId`
- [x] Implement in `MongoWordRepository` in [ebl/dictionary/infrastructure/word_repository.py](ebl/dictionary/infrastructure/word_repository.py)
  - [x] Build full Word document with 17 fields
  - [x] Use `_id` format: "{lemma} I"
  - [x] Set `homonym` to "I"
  - [x] Set `attested` to true
  - [x] Set `origin` to ["EBL"]
  - [x] Initialize empty collections and default strings
  - [x] Insert into Mongo collection
  - [x] Raise duplicate error on duplicate key
- [x] Add repository tests in [ebl/tests/dictionary/test_create_proper_noun.py](ebl/tests/dictionary/test_create_proper_noun.py)
  - [x] Inserts a complete Word document
  - [x] Defaults missing pos to []
  - [x] Uses correct `_id` and homonym
  - [x] Handles duplicate key errors
  - [x] Handles empty pos list
  - [x] Uses correct origin and guide word values

### Phase 3: Service Layer

- [x] Add `create_proper_noun` method to Dictionary service in [ebl/dictionary/application/dictionary_service.py](ebl/dictionary/application/dictionary_service.py)
  - [x] Delegate to repository
- [x] Add service tests in [ebl/tests/dictionary/test_create_proper_noun.py](ebl/tests/dictionary/test_create_proper_noun.py)
  - [x] Service returns new WordId
  - [x] Passes lemma and pos tags through
  - [x] Propagates duplicate error

### Phase 4: Web Layer (HTTP Endpoint)

- [x] Add `ProperNounCreationResource` to [ebl/dictionary/web/words.py](ebl/dictionary/web/words.py)
  - [x] `on_post` method
  - [x] Apply `@falcon.before(require_scope, "create:proper_nouns")`
  - [x] Apply `@validate(ProperNounCreationRequestSchema())`
  - [x] Return `201 Created` with created Word document
  - [x] Handle duplicate errors as `409 Conflict`
- [x] Register route in [ebl/dictionary/web/bootstrap.py](ebl/dictionary/web/bootstrap.py)
  - [x] Add route: `POST /words/create-proper-noun`
- [x] Add endpoint tests in [ebl/tests/dictionary/test_create_proper_noun.py](ebl/tests/dictionary/test_create_proper_noun.py)
  - [x] 201 success response and body
  - [x] 400 validation errors
  - [x] 401 missing auth token
  - [x] 403 missing scope
  - [x] 409 duplicate error
  - [x] Authorization is checked before validation

### Phase 5: Integration & Verification

- [x] Run dictionary test suite with coverage
  - [x] `poetry run pytest ebl/tests/dictionary --cov=ebl/dictionary --cov-report=term-missing`
  - [x] 100% coverage for `ebl/dictionary`
- [ ] Run `task format` and fix issues
- [ ] Run `task lint` and fix issues
- [ ] Run `task test` and fix issues
- [ ] Run `poetry run pyre check` and fix typing issues

### Phase 6: Review & Polish

- [ ] Manual API test via curl
- [ ] Review error messages for clarity
- [ ] Verify README scope references remain accurate
- [ ] Prepare PR summary for review

## Coverage Additions

Additional tests added to close small gaps:

- [x] Akkadian sort edge cases in [ebl/tests/dictionary/test_akkadian_sort.py](ebl/tests/dictionary/test_akkadian_sort.py)
- [x] WordSchema enum normalization in [ebl/tests/dictionary/test_word_schema.py](ebl/tests/dictionary/test_word_schema.py)
- [x] Lemma prefix pipeline and collation in [ebl/tests/dictionary/test_word_repository.py](ebl/tests/dictionary/test_word_repository.py)

## Notes

- Keep the endpoint protected by `create:proper_nouns` scope.
- Follow existing repository and service patterns.
- Ensure new tests are isolated and deterministic.
