<!-- markdownlint-disable MD013 -->
# TASK-743-r13-fix — TODO

Address the findings of the round-13 review in `TASK-743-review.md` on PR #743
(branch `fix-type-checker-blind-spots`).

New task. Does not inherit `TASK-743-review-*` (the review), `TASK-743-fix-*` or
`TASK-743-todo.md`/`TASK-743-log.md`. Own TODO and log, created before work.

## Gate check before starting

- **B2 needs `git merge`/`git rebase`.** Those are on the never-without-asking
  list. I must NOT run them on the strength of "address all the findings" —
  that is not the user asking for that operation in their own words. Stop and
  ask.
- **B1 deletes 23 committed files**, one of which is the review document itself.
  Scope needs confirming before deleting.
- **N2, N3, N4, N5 and the Sourcery thread are edits to the PR on GitHub** —
  outward-facing. Confirm before touching the PR body or threads.
- Nothing is committed or pushed unless asked, per message, every time.

## Steps

- [x] 1. Create TODO + log (this file and `TASK-743-r13-fix-log.md`)
- [x] 2. B3 — map the `nameBreaks`/`subIndex` validation errors to 422 instead of 500
  - [x] 2a. Decide between `DataError` at the raise site vs registering `ValueError` globally
  - [x] 2b. Check layering: does any other domain module raise `DataError`?
  - [x] 2c. Implement; keep `sign_token_base.py` under 250 lines
  - [x] 2d. Tests: 422 for breaks > parts, 422 for negative sub-index, at route level too
- [x] 3. N1 — make `nameBreaks` honest on load so a valid new-format payload is not mis-split
  - [x] 3a. Implement; keep `token_schemas_signs.py` under 250 lines
  - [x] 3b. Tests: legacy still loads, new format with >=2 parts and no breaks loads
- [x] 4. Re-verify the 60-case ATF equivalence probe against the reworked tree (previous run is void after a rewrite)
- [x] 5. Re-run the running-service checks against the reworked tree
- [x] 6. 100% coverage on every changed file — using a correct `--cov` invocation this time
- [x] 7. Gates: `task format`, `task lint`, `task type` (pyre), `task type-pyright`, `task test`, flake8, mypy, `qlty smells --include-tests`, `task lint-md`
- [x] 8. Confirm no new qlty finding introduced; re-diff against the base if anything moved
- [x] 9. ASK: B1 deletion scope, B2 merge authorization, GitHub-facing edits (N2/N3/N4/N5/Sourcery)
- [x] 10. Update `TASK-743-review.md` to reflect what was fixed
- [x] 11. Report — uncommitted, unpushed, unless explicitly asked
