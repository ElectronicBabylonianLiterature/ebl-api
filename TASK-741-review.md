# TASK-741 — Review of PR #741

PR: Fix AfO Register texts-numbers match for references containing spaces
Branch: fix-afo-register-texts-numbers-split → master
URL: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>

## Summary

Two reviewers left feedback:

- **sourcery-ai[bot]** (COMMENTED): one actionable point + an informational
  reviewer's guide.
- **Fabdulla1** (CHANGES_REQUESTED): three findings (resource bound, extra test
  coverage, candidate deduplication).

No inline (diff) review comments exist; all findings live in the review bodies
and the issue-comment reviewer's guide. No branch merged into this one carries
outstanding feedback (the merge commit 7a2d3285 pulled origin/master only).

## Findings

### F1 — Unbounded public endpoint can build very large MongoDB queries

- Source: Fabdulla1 (CHANGES_REQUESTED)
- Severity: **Major** (availability / resource exhaustion)
- File: `ebl/afo_register/web/afo_register_records.py`
- `POST /afo-register/texts-numbers` is public with no validation. The `$or`
  clause count grows with (number of references) × (whitespace tokens − 1) per
  reference, so a large/long payload yields an unexpectedly large Mongo query.
- Reproduction: POST a very long array of long space-separated strings; each
  string of N tokens generates N−1 candidate `$or` clauses, all unbounded.
- **Recommendation / action taken:** Validate the request body at the web
  boundary — reject non-lists, non-string elements, arrays longer than
  `MAX_TEXTS_AND_NUMBERS_QUERIES` (1000), and strings longer than
  `MAX_QUERY_LENGTH` (500) with `DataError` → HTTP 422. Bounding both inputs
  transitively bounds the generated candidate count. Limits are generous versus
  real usage (a fragment's AfO references number in the low tens).

### F2 — Missing test for ambiguous joined reference (multi-match)

- Source: Fabdulla1 (CHANGES_REQUESTED)
- Severity: **Minor** (test coverage / documented behaviour)
- File: `ebl/tests/afo_register/test_afo_register_repository.py`
- Two records e.g. ("A", "B C") and ("A B", "C") both concatenate to "A B C";
  the candidate-split approach should return both. No explicit test protects
  this intended multi-match behaviour.
- **Recommendation / action taken:** Add
  `test_search_by_texts_and_numbers_returns_all_ambiguous_matches` asserting
  both records are returned for `["A B C"]`.

### F3 — Duplicate/overlapping candidates produce repeated `$or` clauses

- Source: Fabdulla1 (CHANGES_REQUESTED)
- Severity: **Minor** (efficiency)
- File: `ebl/afo_register/infrastructure/mongo_afo_register_repository.py`
- Duplicate request strings or overlapping candidate pairs create repeated
  identical `$or` clauses. Results stay correct, but the query is larger and the
  planner does redundant work.
- **Recommendation / action taken:** Deduplicate candidates by
  `(text, textNumber)` in `_build_candidate_query`, preserving first-seen order
  for determinism. Add a test asserting the query is deduplicated.

### F4 — Remove task-tracking scaffolding files before merge

- Source: sourcery-ai[bot] (COMMENTED)
- Severity: **Trivial** (housekeeping)
- **Status: already done** — `TASK-afo-register-link-{log,todo}.md` were removed
  in commit 388a96aa ("Remove task-tracking docs before merge"). No further
  action; confirmed absent from the working tree.

### Informational — Sourcery reviewer's guide

- No action required. Accurately describes the change; no defects raised.

## Data hard-gate check

The only arrays touched are the `$or` candidate list (`List[Dict[str, str]]`,
single shape) and the request body (`List[str]`). Each holds exactly one data
type; dedup and validation preserve that. No mixed-type array, no
discriminate-by-probing, no domain/wire split mismatch. Gate satisfied.

## Reproduction Steps (F1, worst case)

1. `POST /afo-register/texts-numbers` with a JSON array of e.g. 5000 strings,
   each 1000+ chars of space-separated tokens.
2. Before fix: server builds one `$or` with hundreds of thousands of clauses.
3. After fix: request rejected with HTTP 422 before touching Mongo.

## Recommendation

Apply F1–F3 fixes on this branch (done below); F4 already satisfied. Re-run all
gates. Changes are code + tests only; HTTP contract for valid input unchanged.
