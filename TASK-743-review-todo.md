# TASK-743-review — TODO

Review of PR #743 "Make the ATF parser visible to the type checkers"
(`fix-type-checker-blind-spots` -> `master`).

## Scope

Full PR review: fetch **all** existing GitHub feedback (submitted reviews,
inline diff comments, issue/conversation comments, bots — Sourcery, qlty,
Codex — and human reviewers), check CI check runs for failures, check qlty
issues, then review the diff itself against the copilot instruction gates.

## Checklist

- [x] 1. Create TODO + log files (this file and `TASK-743-review-log.md`)
- [x] 2. Gather PR metadata (state, base, head, mergeability, commits)
- [x] 3. Fetch submitted reviews — 2 (sourcery-ai, qltysh), no human reviews
- [x] 4. Fetch inline diff review comments — 6 (1 Sourcery, 5 qlty)
- [x] 5. Fetch issue/conversation comments — 1 (Sourcery reviewer's guide)
- [x] 6. Identify branches merged into this one — only `master`; also pulled
      the related (merged) #740 feedback
- [x] 7. Fetch CI check runs — all green bar one pending `Test Python 3.11`
- [x] 8. Fetch qlty findings — 5 blocking, all pre-existing relocations
- [x] 9. Enumerate the diff — 82 files
- [x] 10. Review diff for correctness, regressions, security, test coverage
- [x] 11. Check the mixed-type-array hard gate — one hit, `NameParts` (F9)
- [x] 12. Check the 250-line gate — largest changed file 249 lines, passes
- [x] 13. Verify locally: booted the service, exercised 8 routes, plus
      in-process checks (Museum enum byte-identical, grammar dir, `reset()`)
- [x] 14. Run the gates — format/lint/pyre/test/flake8/mypy pass;
      **`type-pyright` fails with 149 errors**; coverage 97%
- [x] 15. Cross-check every unresolved external finding — Sourcery and all 5
      qlty items given an explicit disposition in the review
- [x] 16. Write `TASK-743-review.md` — Summary, Findings, Severity,
      Reproduction Steps, Recommendation
- [x] 17. Run `task lint-md` — 0 errors across 13 files
- [x] 18. Re-read the copilot instructions; confirm every gate honoured
- [x] 19. Remind about removing the `TASK-743-*` tracking files before merge

## Constraints

- No commits, no pushes — review only. Report and stop.
- Do not change code unless explicitly requested.

## Status

**Complete.** No source file was modified and nothing was committed. The
working tree holds only `TASK-743-review.md`, `TASK-743-review-todo.md` and
`TASK-743-review-log.md`.

Headline: the ATF-parser diagnosis and fix are sound, pyre and the full suite
are green, but `task type-pyright` fails (149 errors, down from a 173
baseline), the PR does far more than its description says, and six
`TASK-743-*` tracking files are committed and must be removed before merge.
