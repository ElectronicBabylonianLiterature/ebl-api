# TASK-743-review-r2 — TODO

Re-review of PR #743 "Make the ATF parser visible to the type checkers"
(`fix-type-checker-blind-spots` -> `master`).

Scope requested by the user: fetch every review and comment (sourcery-ai,
other bots, human reviewers), check failing CI checks, and check qlty
issues.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before
      reporting complete; state which gates ran and their results.
- [x] No commit, push, or history rewrite unless the user explicitly asks
      in that message. **Nothing was committed.**
- [x] Do not change codebase files — this task is a review only. Only the
      three `TASK-743-review-r2-*.md` files were created.
- [x] Export the review to `TASK-743-review-r2-review.md` using the
      template: Summary, Findings, Severity, Reproduction Steps,
      Recommendation.
- [x] Keep this TODO and `TASK-743-review-r2-log.md` updated as each step
      completes.
- [x] `task lint-md` clean (zero errors and warnings) — 18 files, 0
      errors.
- [x] Check every data-shape change against the mixed-array hard gate —
      see F10 (`NamePart`) and F3 (probe by `getattr`).
- [x] Verify changed behaviour by running the modified backend service
      and the related tests, not tests alone.
- [x] Remind the user to remove `TASK-*` tracking files before merge —
      finding F13.

## Steps

- [x] 1. Identify the PR, branch, head/base SHAs, and diff size.
      #743, `aed3979f` -> `32f6ddae`, 105 files, +5953 / -2966.
- [x] 2. Fetch submitted reviews — 4 (sourcery-ai, qltysh x2, Fabdulla1
      CHANGES_REQUESTED).
- [x] 3. Fetch inline (diff) review comments — 10 (1 sourcery, 9 qlty).
- [x] 4. Fetch issue/conversation comments — 1 (sourcery review guide).
- [x] 5. Fetch feedback for the PRs merged into this branch — #740, #744,
      #745, #747, #748; all resolved in master, none open against #743.
- [x] 6. Fetch CI check runs and statuses — all green; Sourcery skipped
      (diff too large); `qlty check` "8 blocking issues".
- [x] 7. Fetch qlty findings — 9 bot comments, 8 blocking; local
      `qlty smells` unusable (no local config, cloud-configured project),
      so each was verified by hand against the tree.
- [x] 8. Review the diff: correctness, regressions, security, coverage,
      mixed-type arrays, 250-line cap.
- [x] 9. Run the local gates — format, lint, pyre, pyright, tests,
      coverage, flake8, mypy, lint-md. **pyright fails (F2).**
- [x] 10. Run the backend service and exercise the affected routes —
      nine requests, all as expected; the round-1 500 is now 422.
- [x] 11. Reconcile every unresolved external finding in the review file
      — F5–F9 map to Fabdulla1 and sourcery; F8 covers all qlty items.
- [x] 12. Write `TASK-743-review-r2-review.md`.
- [x] 13. Report: gates run, results, findings, nothing committed.

## Outcome

**Request changes.** Two blockers: F1 (merge conflict on the renamed
grammar would drop #749's six manuscript types) and F2 (`task
type-pyright` fails with 19 errors on the PR's own changed set).
