<!-- markdownlint-disable MD013 -->

# TASK-743-r14-review — TODO

Review of PR #743 "Make the ATF parser visible to the type checkers"
(branch `fix-type-checker-blind-spots` -> `master`), round 14.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] Create TODO + log before any work (this file + `TASK-743-r14-review-log.md`)
- [x] Never commit / push / merge / rebase — report only

## Steps

- [x] 1. Identify PR, branch, base, head SHA, diff scope
- [x] 2. Fetch ALL existing feedback: submitted reviews, inline diff comments,
      issue/conversation comments — bots included (Sourcery, qlty, Codex, CodeQL)
- [x] 3. Fetch feedback for any PR whose branch was merged into this one
- [x] 4. Check CI: all check runs / statuses, list failures
- [x] 5. Check qlty verdict (Cloud + local `qlty smells --include-tests`);
      note staleness if local work is unpushed
- [x] 6. Check CodeQL alerts / security scanning results for this PR
- [x] 7. Dev container configuration changes — inspect very carefully, WARN the user
- [x] 8. New `.md` files in the diff — none allowed; flag every one
- [x] 9. Data hard gate: no array holding two data types; no probing
      discriminators; no domain/wire shape mismatch; shared id-space invariants
- [x] 10. File length gate: no `*.py` over 250 lines among changed files
- [x] 11. Coverage of changed files (100% required)
- [x] 12. Run gates locally: format, lint, type (pyre), type-pyright, mypy,
      flake8, test, lint-md
- [x] 13. Run the modified backend service and exercise the affected surface
- [x] 14. Correctness / regression / security / test-coverage review of the diff
- [x] 15. Write `TASK-743-r14-review.md`: metadata header (date, verdict, etc.),
      short friendly human-looking summary first, then `Details` subsection
      listing every finding in full; template sections Summary / Findings /
      Severity / Reproduction Steps / Recommendation
- [x] 16. Remove the markdown line-length limit for the review document so it
      pastes cleanly; keep `task lint-md` green
- [x] 17. Never refer to `khoidt` in the third person — that is the user
- [x] 18. Remind about removing TASK-*.md files before merge
