# TASK-741 — Work Log

## Goal

Fetch all reviews/feedback for PR #741 and address all findings.

## Log

- Created TODO and log files before starting work (task-tracking hard gate).
- Confirmed PR #741 head branch = `fix-afo-register-texts-numbers-split`,
  base = `master`, state OPEN. Local branch in sync with origin.
- Fetched reviews/comments:
  - sourcery-ai[bot] (COMMENTED): remove task-tracking scaffolding files +
    informational reviewer's guide.
  - Fabdulla1 (CHANGES_REQUESTED): F1 bound public endpoint, F2 ambiguous
    multi-match test, F3 dedup candidates.
  - No inline diff comments. Merge commit 7a2d3285 pulled origin/master only,
    so no merged-in-branch feedback outstanding.
- F4 (remove scaffolding) already satisfied in branch commit 388a96aa; the
  TASK-afo-register-link-*.md files are absent from the working tree. Confirmed.

## Implementation

- F3: rewrote `_build_candidate_query` to dedup (text, textNumber) via a `seen`
  set, preserving first-seen order. Added `Set` to typing imports.
- F1: added `validate_texts_and_numbers_query` + constants
  (MAX_TEXTS_AND_NUMBERS_QUERIES=1000, MAX_QUERY_LENGTH=500) in the web resource;
  rejects non-list, non-string elements, over-long arrays/strings with
  `DataError` → HTTP 422 (via existing error_handler mapping). Wired into
  `on_post`.
- F2: added `test_search_by_texts_and_numbers_returns_all_ambiguous_matches`
  (records ("A","B C") and ("A B","C") both match "A B C").
- F3 test: `test_build_candidate_query_deduplicates_candidates`.
- F1 tests: 5 unit tests for the validator branches + a route 422 test.

## Errors / recoveries

- `task type` (pyre) crashed mid-run with `Worker_exited_abnormally` /
  `End_of_file` at ~4720/6605 functions. Diagnosed as OOM: only ~3 GB free in an
  8 GB sandbox, pyre's parallel workers exceed it. Fewer workers got further
  (2 → 5664/6605); `--number-of-workers 1` completed with **No type errors
  found**. Pyre itself passes; the crash was environmental, not a type error.
- `task type-pyright` task does not exist in this repo's Taskfile, and pyright
  is not a poetry tool. Ran pyright via `npx --no-install pyright` (v1.1.411) on
  the changed files → 0 errors.
- First coverage pass left web file at 91% (lines 41-42, 58-59: the
  `except ValueError → NotFoundError` branches in on_get/on_post). on_post is a
  method I edited; covered both branches with mockito `thenRaise(ValueError)`
  route tests (404). Web file now 100%.

## Verification

- Full suite: 3858 passed, 2 skipped, 1 xfailed, 0 failures (290s).
- Targeted coverage: both changed source modules at 100%.
- pyre / pyright / mypy: all clean. flake8 (max-line-length=120): 0. format: clean.
- All four touched *.py files ≤ 250 lines (73 / 151 / 216 / 159).
- Runtime: booted the real `create_app` WSGI app under wsgiref on a real TCP
  socket (mongod via pymongo_inmemory), issued real HTTP requests:
  - `["OrNS 59, 17"]` → 200 with the correct record (space-fix + validation OK)
  - 1001-element array → 422 "Too many queries: at most 1000 allowed."
  - non-list body → 422 "Request body must be a list of strings."
  Throwaway verification test removed afterwards; not part of the change.

## Notes

- Working tree also contains a pre-existing, unrelated uncommitted change to
  `.gitignore` (adds `.qlty`), present before this task (IDE had it open). Left
  untouched — not mine and not a PR finding.
- No commit/push performed (not requested). Changes are uncommitted.
