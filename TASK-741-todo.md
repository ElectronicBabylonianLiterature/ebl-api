# TASK-741 TODO — Review PR #741

PR: [Fix AfO Register texts-numbers match for references containing spaces](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741)
Branch: `fix-afo-register-texts-numbers-split` -> `master`

## Scope

Review-only task. No code changes unless explicitly requested.

## TODO

- [x] 1. Create task TODO and log files (this file + `TASK-741-log.md`)
- [x] 2. Fetch PR metadata (state, mergeability, commits, files changed)
- [x] 3. Fetch the full diff of the PR
- [x] 4. Fetch **all** existing GitHub feedback (HARD GATE):
  - [x] 4a. `gh api repos/.../pulls/741/reviews` — submitted reviews
  - [x] 4b. `gh api repos/.../pulls/741/comments` — inline diff review comments
  - [x] 4c. `gh api repos/.../issues/741/comments` — conversation comments
  - [x] 4d. Identify bot feedback (sourcery-ai, qlty, Codex, others) explicitly
  - [x] 4e. Check for any PR merged **into** this branch; fetch its feedback too
- [x] 5. Fetch check runs / statuses; identify failing checks and read the logs
- [x] 6. Fetch qlty issues for the PR (annotations / check output / local `qlty`)
- [x] 7. Read the changed source and test files in full
- [x] 8. Data hard gate: check every data-shape change for mixed-type arrays,
      probing-based discrimination, domain/wire split mismatch, and
      shared id-space invariants
- [x] 9. File-length gate: confirm no touched `*.py` exceeds 250 lines
- [x] 10. Run local gates on the branch: `task format`, `task lint`, `task type`,
      `task type-pyright`, `task test`, `task lint-md`
- [x] 11. Coverage on changed modules (`--cov-report=term-missing`), 100% required
- [x] 12. `poetry run flake8 <changed> --max-line-length=120`
- [x] 13. `poetry run mypy <changed> --ignore-missing-imports`
- [x] 14. Runtime verification: run the modified backend service and exercise the
      affected AfO Register route (not tests alone)
- [x] 15. Address or acknowledge **every** unresolved step-4 finding in the review
- [x] 16. Write `TASK-741-review.md` using the required template:
      `Summary`, `Findings`, `Severity`, `Reproduction Steps`, `Recommendation`
- [x] 17. Re-read `.github/instructions/copilot.instructions.md`, confirm every
      gate, and state which gates ran and their results
- [x] 18. Remind the user to remove `TASK-741-*.md` before the PR is merged

## Constraints

- No `git commit` / `git push` / `gh pr` write operations without an explicit request.
- Do not modify code unless explicitly requested.
