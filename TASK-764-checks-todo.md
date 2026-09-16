# TASK-764-checks TODO — Verify remote checks and the release ordering

Branch `migrate-name-breaks`, pushed head `24ff519b`.

Status legend: `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-checks-todo.md`
- [x] Create `TASK-764-checks-log.md`
- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting
      complete

## 1. Remote checks on `24ff519b`

- [x] Confirm the push landed and the PR head moved
- [x] Poll every check to completion
- [x] Report every check by name with its conclusion
- [x] Investigate any failure: pull the job log and explain the root cause
- [x] Re-fetch Sourcery review + inline comments on the new commit
- [x] Re-fetch qlty check / coverage / coverage-diff statuses
- [x] Re-fetch CodeQL result
- [x] Note any check that is merely "pending" vs genuinely failing

## 2. Verify the proposed ordering

- [x] Identify the repository and state of frontend #817 `add-name-breaks`
- [x] Confirm it is 7 files and independent
- [x] Verify the claim that the frontend must deploy BEFORE ebl-api #743
- [x] Identify `chore/ts7-tsconfig-migration` and its PR, if any
- [x] Identify #774 `chore/remove-bluebird`, its repo and its failing check
- [x] Verify the claim that rebasing #774 picks up a test fix that turns the
      check green
- [x] Check whether anything is MISSING from the ordering — in particular where
      PR #764 (this migration) and the adapter-deletion PR belong
- [x] Give a clear verdict on each numbered step

## 3. Close out

- [x] Report findings
- [x] Do NOT commit or push — not authorised in this message
