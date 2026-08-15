# TASK-735 TODO — Review PR #735 (Realia ID listing endpoint)

Branch: `add-realia-slugs-endpoint` → `master`
PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735>

## Steps

- [x] 1. Create task TODO and log files (this file + `TASK-735-log.md`)
- [x] 2. Fetch PR metadata (state, mergeability, base/head, files changed)
- [x] 3. Fetch ALL submitted reviews (`/pulls/735/reviews`)
- [x] 4. Fetch ALL inline diff review comments (`/pulls/735/comments`)
- [x] 5. Fetch ALL issue/conversation comments (`/issues/735/comments`)
- [x] 6. Identify bot reviewers (Sourcery AI, qlty, Codex, Copilot, others)
      and capture every finding from each
- [x] 7. Check for any PR merged into this branch and fetch its feedback too
- [x] 8. Fetch CI check runs / statuses; list every failing check with detail
- [x] 9. Fetch qlty findings specifically (annotations / check output)
- [x] 10. Read the full diff of all changed files
- [x] 11. Review against the data hard gate (one array = one type; no
       probing discriminators; no domain/wire shape mismatch; shared id
       space invariants across separated arrays)
- [x] 12. Review against coding standards (250-line file limit, type hints,
       no `Any`, full names, small functions, no stray comments)
- [x] 13. Check test coverage of changed files (100% required, including
       pre-existing gaps on touched lines)
- [x] 14. Run local gates for review evidence: format, lint, pyre, pyright,
       mypy, flake8, tests + coverage on changed modules
- [x] 15. Verify changed behaviour by RUNNING the backend service and
       exercising the affected route (not tests alone)
- [x] 16. Address or explicitly acknowledge EVERY unresolved existing finding
       in the review file
- [x] 17. Write `TASK-735-review.md` with the required template sections:
       Summary, Findings, Severity, Reproduction Steps, Recommendation
- [x] 18. Re-read copilot instructions; confirm every gate honoured; report
       gate results
- [x] 19. Remind user to remove TASK-735-*.md files before merge
- [x] 20. Report without committing (no commit/push unless explicitly asked)

## Notes

- Merge state reported as CONFLICTING at review start — must be flagged.
- No commits, pushes, or PR mutations are part of this task.
