# TASK-741-fix Work Log

## Task

Address every finding raised in `TASK-741-review.md` for PR #741 (L1, L2, L3,
I1, I2).

## Entries

### Start

New task, so new tracking artefacts: created `TASK-741-fix-todo.md` and this log
before making any code change. The previous task's `TASK-741-*.md` files stay in
place — they are the review this task acts on, and the PR is not merging yet.

### Reading the history first — and finding my own review half-wrong

Before touching `MAX_CANDIDATES` I read `git show 5b716e5b`. Its message
documents why the cap is 10,000: a 504 KB body that passed the request limits
previously expanded to 166,000 `$or` clauses and an **85 MB BSON filter**, past
MongoDB's 16 MB document limit, and the endpoint answered 500. The cap sizes the
worst surviving case at about 4.8 MB.

This makes one of the two options my own L1 finding offered — raise
`MAX_CANDIDATES` to `1000 * 23 = 23000` — **wrong**: it would put the worst case
back around 11 MB. Recorded this in the review rather than quietly picking the
other option, because the finding as written would have led a reader astray.

The correct direction is the reverse: make the *route* consistent with the cap.

### L1 + I1 — candidate budget validated at the route

- `TOO_MANY_CANDIDATES_MESSAGE` added to the repository module as the single
  source of the wording, now naming the batch rather than "Query".
- `count_candidate_splits` and `validate_candidate_budget` added to
  `afo_register_records.py`; `validate_texts_and_numbers_query` now runs the
  budget check after per-query validation.
- Because the repository deduplicates, its candidate count is always ≤ the
  route's estimate, so a route-validated request can no longer trip the
  repository bound. The inconsistency is closed by construction rather than by
  loosening a safety limit.
- The repository check stays as a backstop for direct callers. It is no longer
  reachable through the route but is still covered by the two repository-level
  tests, so coverage stays at 100%.
- Tests added: `test_count_candidate_splits_counts_split_points`,
  `test_validate_candidate_budget_accepts_the_largest_allowed_batch`,
  `test_validate_candidate_budget_rejects_an_over_broad_batch`,
  `test_search_by_texts_and_numbers_route_accepts_the_largest_allowed_batch`.
  The pre-existing over-broad route test still passes and now also asserts the
  message. A local `build_maximal_queries` helper replaced the inline query
  construction that was duplicated across those tests.

### L2 — established the facts before choosing

The review suggested annotating `candidate_splits(query: str)` while keeping the
runtime guard. I tried it before recommending it: pyright then fails with
`Argument of type "None" cannot be assigned to parameter "query" of type "str"`
on the existing `test_candidate_splits_rejects_non_string`. So the narrowing
costs either a `cast`/suppression or the deletion of a test — neither allowed
without asking.

Reverted the experiment and put the trade-off to the user with three options.
User chose: keep `object`, but **raise** instead of returning `[]`. Implemented:

- `NON_STRING_QUERY_MESSAGE` added to the repository module and reused by the
  route's `validate_query`, so both layers report identically.
- `candidate_splits` raises `DataError` on a non-string.
- `test_candidate_splits_rejects_non_string` updated in place from `== []` to
  `pytest.raises(DataError)`. **No test was removed.**

This closes a real silent-coercion hole: calling the repository directly with
`["A B", 5]` previously dropped the `5` and answered as though only `"A B"` had
been asked for.

### L3 — PR body

Asked before editing, since the PR description is outward-facing. User approved
updating the stale filenames. Patched **only** the "Before merge" section via
`gh api repos/... -X PATCH -F body=@file` (`gh pr edit --body` fails silently in
this repo), after showing the exact diff. Verified the change landed remotely.

The task files themselves stay until merge — deleting them now would destroy the
tracking for the task in progress.

### I2 — acknowledged, no code change

Whitespace normalization is query-side only. Both available fixes (normalizing at
import, or matching a normalized projection) are out of scope for this PR, and
the second would give up the compound index that P1 confirms is in use. Behaviour
is unchanged from what shipped before, so I left it alone and recorded the
rationale under the finding.

### Errors made and recovered

1. **Added a test that violated the project's own data hard gate.** I wrote
   `test_build_candidate_query_rejects_non_string` passing `["A B", 5]` — two
   types in one array. `task type-pyright` rejected it:
   `Argument of type "list[str | int]" cannot be assigned to parameter
   "query_list" of type "Sequence[str]"`. Removed the test; it was one I had just
   added, added nothing to coverage, and the `candidate_splits(None)` test
   already covers the raise. The type checker caught what I should have caught
   while writing it.
2. **My own L1 finding contained a wrong recommendation** (raising
   `MAX_CANDIDATES`), as described above. Corrected in the review rather than
   silently avoided.

### Gate runs (current tree)

| Gate | Result |
| ---- | ------ |
| `task format` | 802 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `mypy` on 4 changed files | Success: no issues found |
| `flake8 --max-line-length=120` | exit 0, no output |
| `pytest` + `--cov` on `afo_register` | 49 passed, **100%** coverage |
| 250-line file limit | 162, 93, 223, 75, 205 — all pass |
| `task lint-md` | 0 errors across 9 files |
| Full suite | **4323 passed, 2 skipped, 1 xfailed, 0 failed** |

### Runtime re-verification (hard gate)

The implementation changed, so the previous task's runtime evidence was void.
Restarted the service from the current tree (confirmed by process start time) and
re-ran all 16 request bodies plus the two L1 boundary cases. Results are in the
review's `Reproduction Steps`. Key deltas from the earlier run:

- 435 maximal queries → `422 "The submitted queries expand to more than 10000
  text and number combinations."` (was "Query is too broad…", and was raised in
  the repository rather than the route)
- 434 maximal queries → `200 []`, unchanged, now pinned by a test
- `["A B", 5]` → `422 "Each query must be a string."` from the shared constant

All original behaviour — the `OrNS 59, 17` fix, the `59, 170` decoy exclusion,
ambiguous multi-match, dedup, whitespace normalization, and partial-match
rejection — unchanged.

### Not committed

No `git commit`, `git push`, or history-changing command was run. The only remote
change is the approved PR-body patch.
