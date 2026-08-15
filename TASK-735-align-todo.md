# TASK-735-align TODO — Align the backend stub rule with the frontend

Decision taken: change the backend so its "does this entry have own
content" test matches `hasOwnContent` in ebl-frontend
`src/realia/domain/RealiaEntry.ts`, so the sitemap lists exactly the
pages that do not redirect.

## Steps

- [x] 1. Create this TODO and `TASK-735-align-log.md` before any change
- [x] 2. Confirm how the frontend maps `reallexikon[].reference`, to check
      that the backend's resolvable-reference test really is equivalent
      to the frontend's `reference !== null`
- [x] 3. Remove `relatedTerms`, `type`, `wikidataId` from
      `OWN_CONTENT_ARRAY_FIELDS`
- [x] 4. Add the frontend's `reallexikon.length > 1` condition
- [x] 5. Decouple `realia_document_shape.ARRAY_FIELDS` from
      `OWN_CONTENT_ARRAY_FIELDS` — the malformed-shape guard must still
      cover every array field in the schema, including the three removed
      from the content test
- [x] 6. Update the affected tests and add coverage for the new rule
- [x] 7. Re-run the rule-comparison script; every shape must agree
- [x] 8. Gate: `task format`
- [x] 9. Gate: `task lint`
- [x] 10. Gate: `task type` (pyre)
- [x] 11. Gate: `task type-pyright`
- [x] 12. Gate: `task test` (full suite)
- [x] 13. Gate: coverage 100% on changed modules
- [x] 14. Gate: `flake8` and `mypy` on changed modules
- [x] 15. Gate: `task lint-md`
- [x] 16. Re-verify against the running service — previous runs are void
- [x] 17. Update `TASK-735-review.md` to close Finding 5
- [x] 18. Re-read copilot instructions and confirm every gate
- [x] 19. Make NO commits; report and remind about the TASK files

## Open, not decided

- The completely empty entry (no cross-references, no content) is still
  listed. Raised separately; no change made without a decision.

## Notes

- Commit authorisation was single-use and is spent. No commits.
