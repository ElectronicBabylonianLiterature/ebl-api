# Proper Noun Creation Endpoint - Backend Implementation Log

**Date Started:** February 12, 2026  
**Branch:** create-personal-pronouns  
**Task:** Implement `POST /words/create-proper-noun` endpoint to persist newly created proper nouns

## Summary

Backend implementation of proper noun creation feature. Users can create and persist new proper noun Word documents through a RESTful API endpoint. The implementation follows existing architecture patterns: repository abstraction -> service layer -> web endpoint.

## Database Schema Reference

Proper noun documents follow this structure:
- `_id`: "{lemma} I" (unique identifier combining lemma and homonym)
- `lemma`: [lemma] (array with single string)
- `homonym`: "I" (always "I" for proper nouns)
- `pos`: [pos_tags] (array with zero or more POS codes like DN, GN, PN, N)
- `attested`: true (proper nouns are attested by default)
- `meaning`: "" (empty string, can be updated later)
- `origin`: ["EBL"] (marks as user-created content)
- Empty collections: forms, logograms, derived, amplifiedMeanings, oraccWords, roots

## Authorization & Security

**Scope Required:** `create:proper_nouns`

This endpoint is protected and restricted to users with the `create:proper_nouns` authorization scope in their Auth0 token. This scope is defined in Auth0 as part of the ebl-api API permissions.

**Access Control:**
- Users WITH `create:proper_nouns` scope -> Endpoint accessible (201 Created on success)
- Users WITHOUT `create:proper_nouns` scope -> 403 Forbidden
- Requests with invalid/missing auth token -> 401 Unauthorized

**Implementation Details:**
- Use `@falcon.before(require_scope, "create:proper_nouns")` decorator on the endpoint
- The decorator is applied BEFORE validation, so authorization is checked first
- See [Auth0 configuration in README.md](README.md#auth0) for scope setup details
- See [Authentication & Authorization section in README.md](README.md#authentication-and-authorization) for decorator usage patterns

## Implementation Progress

### Phase 1: Schemas & Data Validation
**Status:** Complete
**Details:** Added ProperNounCreationRequestSchema to validate incoming requests
**Tests:** Schema validation tests - testing required fields, array validation, error cases

### Phase 2: Repository Layer
**Status:** Complete
**Details:** Extended WordRepository and implemented create_proper_noun in MongoWordRepository
**Tests:** Repository tests - testing successful creation, field structure, duplicate handling, edge cases

### Phase 3: Service Layer
**Status:** Complete
**Details:** Added create_proper_noun to Dictionary service, delegating to repository
**Tests:** Service tests - verifying delegation and error propagation

### Phase 4: Web Endpoint
**Status:** Complete
**Details:** Added ProperNounCreationResource with authorization and validation
**Tests:** Endpoint tests - 201 success, validation errors, auth failures, duplicate handling

### Phase 5: Coverage Additions
**Status:** Complete
**Details:** Added targeted tests to reach 100% coverage for ebl/dictionary
**Tests Added:**
- Akkadian sort edge cases for `_split_prefix_and_roman`
- WordSchema enum normalization branches
- Lemma prefix pipeline and collation behavior

### Phase 6: Verification
**Status:** In Progress
**Details:** Verify format, lint, type check, and test tasks on current branch

## Implementation Notes

- POS tags are optional; default to [] when omitted.
- Proper noun `_id` is `"{lemma} I"` and `homonym` is always "I".
- `origin` is always ["EBL"] to mark user-created content.
- Authorization must be checked before validation (decorator order).

## Test Summary

- Schema: 10 tests
- Repository: 13 tests
- Service: 6 tests
- Web endpoint: 16 tests
- Coverage additions: 7 tests
- Total added: 49 tests

**Current Dictionary Test Suite:** 198 passing, 100% coverage for ebl/dictionary

## Remaining Work

- Run `task format` and fix issues
- Run `task lint` and fix issues
- Run `task test` and fix issues
- Run `poetry run pyre check` and fix typing issues
- Manual API verification (curl)
