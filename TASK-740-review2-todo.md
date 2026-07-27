# TASK-740-review2 — TODO

Review of PR #740 "Realia annotation API: resolve realiaInfo on every
fragment-returning route" (`add-realia-annotation-api` -> `master`).

A previous review task exists (`TASK-740-review.md`); per the task-tracking hard
gate, this is a **new** task and gets its own TODO / log / review files.

## Checklist

- [x] 1. Create TODO and log files (this file + `TASK-740-review2-log.md`)
- [x] 2. Fetch **all** existing GitHub feedback on PR #740
  - [x] 2a. `gh api repos/.../pulls/740/reviews`
  - [x] 2b. `gh api repos/.../pulls/740/comments` (inline diff comments)
  - [x] 2c. `gh api repos/.../issues/740/comments` (conversation)
  - [x] 2d. Bot feedback (Sourcery, qlty, Codex) included, not filtered out
  - [x] 2e. Identify any PR whose branch merged into this one; fetch its feedback
  - [x] 2f. Record every unresolved finding; each must be addressed or
        acknowledged with a rationale in the review file
- [x] 3. Read the full diff vs merge-base
- [x] 4. Data hard gate audit (mixed-type arrays)
  - [x] 4a. Every array / id list holds exactly one data type
  - [x] 4b. No type discriminated by probing an optional field
  - [x] 4c. No shape split in the domain but merged on the wire, or the reverse
  - [x] 4d. Shared id-space invariants (uniqueness, existence, referential
        integrity) enforced across the **union** of the separated arrays
- [x] 5. 250-line hard gate: every changed `*.py` file, source and test
- [x] 6. Coding standards: full names, type hints, no stray `Any`, small
      functions, no unrequested comments, no lint/format config edits
- [x] 7. Correctness / regression / security / coverage review of the diff
- [x] 8. Run the gates
  - [x] 8a. `task format`
  - [x] 8b. `task lint`
  - [x] 8c. `task type` (pyre — the CI gate) — **FAILS** (Finding 1)
  - [x] 8d. `task type-pyright` — **FAILS** (Finding 2)
  - [x] 8e. `task test`
  - [x] 8f. coverage on changed modules (100% required)
  - [x] 8g. `poetry run flake8 <changed> --max-line-length=120`
  - [x] 8h. `poetry run mypy <changed> --ignore-missing-imports`
        — **FAILS** (Finding 4)
  - [x] 8i. `task lint-md`
- [x] 9. Runtime verification: run the modified backend service and exercise the
      affected routes (not tests alone)
- [x] 10. Write `TASK-740-review2.md` with sections: Summary, Findings,
      Severity, Reproduction Steps, Recommendation
- [x] 11. Re-read `.github/instructions/copilot.instructions.md` and confirm
      every section honoured; state which gates ran and their results
- [x] 12. Remind the user to remove the TASK-740 `.md` tracking files before the
      PR is merged (they are currently committed on the branch)
- [x] 13. Report without committing or pushing anything
