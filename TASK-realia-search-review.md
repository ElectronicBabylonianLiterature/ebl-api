# TASK-realia-search — Review

## Summary

`GET /realia` search crashed because `RealiaEntrySchema` did not match the real
`realia` collection. Two stored fields differ from the schema: `type` (free-text
strings, not the `RealiaType` enum) and `reallexikon[].reference` (a bibliography
-id string, not a nested object). The schema and domain model were aligned to the
stored data (the source of truth), and tests/factory updated accordingly.

## Findings

1. **`type` stored as free-text category strings**;
   `NameEnumField(RealiaType)` raised "Invalid value."
   Severity: High (endpoint 500). Status: fixed.
2. **`reallexikon[].reference` stored as a bibliography-id string**;
   `fields.Nested` raised "Invalid input type."
   Severity: High (endpoint 500). Status: fixed.
3. **Pre-existing `mypy` errors in `ebl/common/domain/scopes.py`.**
   Severity: Low (pre-existing, unrelated).
   Status: not addressed — needs decision.
4. **Real docs carry data dropped on load**: `lemma`, `realiaId`,
   `crossReferences`, `afoCrossReferences`, `afoRegister[].id`.
   Severity: Info. Status: out of scope.

## Severity

- Findings 1 & 2 are correctness/regression bugs that made both `GET /realia/{id}`
  and `GET /realia` (search) unusable against production data.

## Reproduction Steps

1. Point the API at the real `ebldev` database.
2. `task start`, then `GET /realia?query=Bürger`.
3. Before fix: `marshmallow.ValidationError` (rows 1, 7, 9, 11, 12, 13) → 500.
4. After fix: 200 with 6 entries; reallexikon references include their
   bibliography document.

## Recommendation

- Findings 1 & 2: ship the fix (done).
- Finding 3: address `scopes.py` mypy errors in a separate, dedicated change so
  this bugfix stays scoped. Decision needed from the maintainer.
- Finding 4: if the frontend needs `lemma`/cross-references, model them as a
  follow-up feature (add fields to the domain + schema with tests).

## Cleanup reminder

Before merge, remove the task tracking files:
`TASK-realia-search-todo.md`, `TASK-realia-search-log.md`,
`TASK-realia-search-review.md`. Also note the leftover `TASK-719-*.md` files in
the working tree from a prior task.
