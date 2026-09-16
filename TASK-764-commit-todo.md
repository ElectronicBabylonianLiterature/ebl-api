# TASK-764-commit TODO — Commit the outstanding task documentation

Branch `migrate-name-breaks`. Previous commit `24ff519b` is **pushed**, so this
must be a NEW commit, never an amend.

Status legend: `[ ]` pending, `[x]` done.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-commit-todo.md`
- [x] Create `TASK-764-commit-log.md`
- [x] Write the closing log entries BEFORE committing, so nothing is left
      uncommitted afterwards — the mistake made on the first amend
- [ ] Re-read `.github/instructions/copilot.instructions.md` before reporting

## 1. Confirm it must be a new commit

- [x] `git ls-remote` shows `24ff519b` on the remote
- [ ] Therefore: no `--amend`, no rewrite of pushed history

## 2. Pre-commit hard gates (in order, all must pass)

- [ ] 1. `task format`
- [ ] 2. `task lint`
- [ ] 3. `task type` (pyre)
- [ ] 4. `task type-pyright`
- [ ] 5. `task test`
- [ ] 6. coverage on changed modules — 100%
- [ ] 7. `poetry run flake8 <changed modules> --max-line-length=120`
- [ ] 8. `poetry run mypy <changed modules> --ignore-missing-imports`
- [ ] `task lint-md` — the change is markdown only, so this is the one that
      actually exercises it

## 3. Commit (explicitly authorised in this message; single use)

- [ ] Stage everything
- [ ] Commit
- [ ] Verify the working tree is clean afterwards
- [ ] Do NOT push — not requested in this message

## 4. Close out

- [ ] Report which gates ran and their results
- [ ] Remind to remove every `TASK-764*.md` file before the PR merges
