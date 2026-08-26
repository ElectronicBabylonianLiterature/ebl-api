<!-- markdownlint-disable MD013 -->

# TASK-743-review2 — TODO

Review of PR #743 "Make the ATF parser visible to the type checkers"
(branch `fix-type-checker-blind-spots` -> `master`).

## Checklist

- [x] 1. Create task TODO + log files (this file and `TASK-743-review2-log.md`)
- [x] 2. Fetch PR metadata, state, mergeability
- [x] 3. Fetch ALL submitted reviews (`/pulls/743/reviews`)
- [x] 4. Fetch ALL inline/diff review comments (`/pulls/743/comments`)
- [x] 5. Fetch ALL issue/conversation comments (`/issues/743/comments`)
- [x] 6. Identify bot reviewers (sourcery-ai, qlty, Codex, Copilot, others) and capture every finding
- [x] 7. Fetch feedback for any PR whose branch was merged into this one
- [x] 8. Fetch CI check runs / statuses; identify failing checks
- [x] 9. Fetch qlty issues for the PR
- [x] 10. Review the full diff (`git diff master...HEAD`)
- [x] 11. HARD GATE: check every data-shape change against the mixed-type-array gate
- [x] 12. HARD GATE: check `*.py` 250-line cap on every changed file
- [x] 13. Check dev container configuration changes -> WARN THE USER explicitly, check very carefully
- [x] 14. Check that no new `.md` files are added by the PR
- [x] 15. Run gates locally: `task format`, `task lint`, `task type`, `task type-pyright`, `task test`
- [x] 16. Coverage check on changed modules (100% on changed lines)
- [x] 17. `poetry run flake8 <changed> --max-line-length=120`
- [x] 18. `poetry run mypy <changed> --ignore-missing-imports`
- [x] 19. HARD GATE: verify changed behaviour by running the backend service and exercising affected surface
- [x] 20. Write `TASK-743-review.md` with template sections + friendly human-looking summary first + `Details` subsection
- [x] 21. Remove the line-length limit in the review document so it can be posted as-is
- [x] 22. Report: gates run + results, no commits made, remind to delete TASK-*.md before merge
