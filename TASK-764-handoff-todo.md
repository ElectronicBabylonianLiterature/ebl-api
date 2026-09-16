# TASK-764-handoff TODO — Update documentation and handoff, then commit

Follow-up to `TASK-764-fix`. Branch `migrate-name-breaks`, base commit
`aaffba18`.

Status legend: `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-handoff-todo.md`
- [x] Create `TASK-764-handoff-log.md`
- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting
      complete

## 1. Documentation

- [x] Write `TASK-764-handoff.md`: what was done, what remains, next steps
- [x] Record every finding that is NOT fully addressed, with the reason
- [x] Record the stale parts of the PR body that still need editing
- [x] Record the deployment ordering constraint (#743 first) prominently
- [x] Confirm `TASK-764-review.md` Resolution section is current
- [x] Confirm `TASK-764-fix-log.md` and `TASK-764-fix-todo.md` are current
- [x] `task lint-md` clean

## 2. Pre-commit hard gates (in order, all must pass)

- [x] 1. `task format`
- [x] 2. `task lint`
- [x] 3. `task type` (pyre — the gate CI enforces)
- [x] 4. `task type-pyright`
- [x] 5. `task test`
- [x] 6. `poetry run pytest <changed modules> --cov=... --cov-report=term-missing`
      — 100%
- [x] 7. `poetry run flake8 <changed modules> --max-line-length=120`
- [x] 8. `poetry run mypy <changed modules> --ignore-missing-imports`

## 3. Commit (explicitly authorised in this message; single use)

- [x] Stage ONLY the four source/test files — no `TASK-*.md` files, because the
      standing instruction for this PR is that it must add no `.md` files
- [x] Verify `git status` shows the task markdown still untracked
- [x] Commit with a message describing the review fixes
- [x] Do NOT push unless separately asked — but check `git ls-remote` first,
      because commits in this environment have reached GitHub without a push

## 4. Remote checks

- [x] Confirm whether the commit reached the remote
- [!] If it did: wait for the checks and report every one of them
- [x] If it did not: stop and ask before pushing
- [!] Re-fetch Sourcery / qlty / CodeQL feedback on the new commit

## 5. Close out

- [x] Report which gates ran and their results
- [x] Remind to remove all `TASK-764*.md` files before the PR merges
