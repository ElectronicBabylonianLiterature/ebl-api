<!-- markdownlint-disable MD013 -->
# TASK-743-review — TODO

Review round 13 of PR #743 "Make the ATF parser visible to the type checkers"
(branch `fix-type-checker-blind-spots` → `master`).

This is a **new task**. It does not inherit `TASK-743-todo.md` / `TASK-743-log.md`
(round 12) or `TASK-743-fix-*` (the fix task). Per the task-tracking hard gate,
this task gets its own TODO and log, created before any review work began.

## Deliverable

- Update `TASK-743-review.md` in place (no new review `.md` file).
- Required sections: metadata header (date, verdict, etc.), a short friendly
  human-looking summary **first**, then a `Details` subsection listing every
  finding in full.
- `<!-- markdownlint-disable MD013 -->` at the top so the document has no line
  length limit and can be pasted into GitHub cleanly.
- The repository owner's GitHub username is the user's own; never write it as a third party.

## Steps

- [x] 1. Create TODO + log (this file and `TASK-743-review-log.md`)
- [x] 2. Fetch remote; confirm local `HEAD` == remote branch head (stale-verdict rule)
- [x] 3. Establish merge base and full diff stats vs `master`
- [x] 4. Read the PR body and description claims
- [x] 5. Fetch ALL GitHub feedback: submitted reviews, inline diff comments, issue/conversation comments — Sourcery-AI, qlty, Codex, CodeQL, any human reviewer
- [x] 6. Fetch feedback for any PR whose branch was merged into this one
- [x] 7. Check every check run / status: list failures explicitly
- [x] 8. qlty — Cloud verdict + local `qlty smells --all --include-tests` at HEAD vs `origin/master` worktree, diffed
- [x] 9. CodeQL — fetch code-scanning alerts for the branch
- [x] 10. **Dev container configuration diff — warn the user if anything changed; scrutinise very carefully**
- [x] 11. New `.md` files added by the PR — must be none; report any
- [x] 12. Verify each round-12 finding (F1, F2, F3 blocking; F4–F14) against the current tree
- [x] 13. Data hard gate: any array holding two data types, id lists, probing discriminators, domain/wire shape mismatch, shared id-space invariants
- [x] 14. File-length hard gate: no `*.py` over 250 lines among changed files
- [x] 15. Run the gates locally: format, lint, pyre, pyright, test, coverage, flake8, mypy
- [x] 16. Run the modified backend service and exercise the affected routes
- [x] 17. Confirm no tests were silently dropped between merge base and HEAD
- [x] 18. Write the review document; re-read copilot instructions and confirm every gate
- [x] 19. Report — no commit, no push (not requested)
