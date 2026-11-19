# TASK chapter-edit-lite: TODO

Goal: make the corpus chapter edit page load in seconds for large chapters.
This repository holds the API half; the page itself is in ebl-frontend.

## Done

- [x] `GET {chapter}/outline`: light chapter outline
- [x] `GET {chapter}/lines?offset=&limit=&tokens=`: lines in edit shape
- [x] `POST {chapter}/lines?view=outline`: light save response
- [x] Shared ATF helpers in `ebl/corpus/domain/line_atf.py`
- [x] Tests: domain, schemas, pagination, repository, routes
- [x] `ruff format --check ebl scripts`
- [x] `ruff check ebl scripts`
- [x] `pyre check`
- [x] `pyright`, `flake8`, `mypy` on the changed modules
- [x] Full `pytest` with the CI test environment
- [x] 100 % coverage of every new or changed module
- [x] Timed against Enūma eliš I replayed from production

- [x] Step 1: review notes on pull request #827
  - [x] qlty: responders take `**chapter`; two tests take one case object
  - [x] Chapter revision on reads; stale saves and stale pages get 409
  - [x] `qlty smells --include-tests` on the changed files: no findings
  - [x] `task lint-md` (markdownlint): 0 errors
- [x] Step 2 (frontend only): reduced to the split view

## Open

- [ ] Save path on real data (the sandbox database has no sign list)

## Later tasks

- [ ] Sparse alignment and lemmatization saves keyed by line index
- [ ] Faster write path: update only the changed line
- [ ] Revision check on save (409 on conflict)

## Next phase (decided after the mock-ups)

Chosen version: C, split view. Model: Fable 5.2.

1. Fix the notes on the open pull requests (ebl-api #827, ebl-frontend
   #869):
   - qlty: too many parameters in two route handlers and two tests; too
     many returns in `findKeyTarget` and `editLiteReducer`.
   - Sourcery: chapter revision on reads and 409 on stale saves; skip
     token parsing when `tokens=false`; run `task lint-md`.
2. Reduce the frontend to the split view; remove versions A, B, D and the
   version switcher.
3. Full editor: add and delete for lines, variants and manuscript lines;
   Import tab; real saving in the Manuscripts tab; unsaved-changes
   warning; hide editing without write permission.
4. New rule, move lines: an editor can change the placement of a line in
   the chapter. The whole line moves intact, with its variants,
   manuscript lines, alignment and lemmatization.
   - Today saves address lines by array position and new lines are only
     appended, so a line cannot be moved.
   - Needs an API operation that moves the stored line (not delete and
     re-add), the revision check from step 1, and a control in the split
     view (move up or down, or move after line N).
   - To decide: whether line numbers are renumbered when a line moves.
5. Alignment and lemmatization per line, with per-line save endpoints and
   batched word lookups.
6. New rule, keep existing alignments per manuscript line: if a
   manuscript line already has alignments, the alignment editor does not
   try to align that manuscript line again.
   - No automatic suggestions are computed for it and none of its
     alignments is overwritten.
   - Other manuscript lines of the same line that have no alignment still
     get automatic suggestions.
   - To decide: whether a re-align button per manuscript line is wanted.
7. Faster saving on the server: rewrite only the changed line.
8. Replace the classic page at `/edit`; remove the old components and the
   legacy data source. The `craco.config.js` coverage list edit needs
   approval.

Estimate: about 22 to 37 hours of work in total.

## Where to use Fable 5.2 with Ultracode

Use Ultracode (several agents plus an independent check of every finding)
only where a mistake is costly and hard to see:

- Step 4, moving lines, together with the revision and 409 check: a
  mistake silently changes the wrong line in the stored chapter.
- Step 6, the alignment rule: the existing suggestion code is intricate
  and easy to break.
- The final review before step 8 replaces the classic page.

Use a single agent without Ultracode for steps 1, 2, 3, 5 and 7: they are
well defined and the test suites catch most mistakes.

Today's mock-up phase ran entirely with Ultracode and took four to five
5-hour usage windows. Limiting Ultracode to the parts above should roughly
halve usage: expect about 5 to 8 windows for the whole next phase.

## Before merge

- [ ] Remove `TASK-chapter-edit-lite-todo.md`
- [ ] Remove `TASK-chapter-edit-lite-log.md`
