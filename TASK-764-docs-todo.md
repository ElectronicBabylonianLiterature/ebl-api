# TASK-764-docs TODO — Commit the docs and update the PR body

Follow-up to `TASK-764-handoff`. Branch `migrate-name-breaks`, local head
`ab66d7de` (unpushed).

Status legend: `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-docs-todo.md`
- [x] Create `TASK-764-docs-log.md`
- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting
      complete

## 1. PR body

- [x] Fetch the current PR body
- [x] Correct the stored-path claim: the code recurses on the `nameParts` key,
      it does not walk `text.lines[].content[].parts[]`
- [x] Add the grammar argument for why the even/odd split is guaranteed
- [x] Describe the concurrency behaviour introduced by the F1 fix
- [x] Say that `--apply` is resumable and what to do after an abort
- [x] Refresh the Verification table for the post-fix behaviour
- [x] Note that `MONGODB_DB` is now required
- [x] Note the pyre crash so nobody "tidies" the typing back
- [x] Preserve the existing "Summary by Sourcery" section
- [x] Patch via `gh api ... -X PATCH -F body=@file`, since `gh pr edit --body`
      fails silently in this environment
- [x] Verify the body actually changed on GitHub

## 2. Documentation

- [x] Update `TASK-764-handoff.md`: the PR body item moves from open to done
- [x] Update `TASK-764-review.md` if any finding status changes
- [x] `task lint-md` clean

## 3. Pre-commit hard gates (in order, all must pass)

- [x] 1. `task format`
- [x] 2. `task lint`
- [x] 3. `task type` (pyre)
- [x] 4. `task type-pyright`
- [x] 5. `task test`
- [x] 6. coverage on changed modules — 100%
- [x] 7. `poetry run flake8 <changed modules> --max-line-length=120`
- [x] 8. `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] `task lint-md` (markdown is being committed this time)

## 4. Amend the commit (explicitly authorised in this message; single use)

- [x] Confirm `ab66d7de` is still unpushed before amending — amending a pushed
      commit is forbidden without a specific request
- [x] Stage every `TASK-764*.md` file
- [x] `git commit --amend`
- [x] Verify the tree is clean afterwards — failed on the first amend, which
      left this log and TODO modified; fixed by a second amend taking everything

## 5. Close out

- [x] Report which gates ran and their results
- [x] Do NOT push — not requested in this message
- [x] Note that the task markdown is now IN the PR and must be removed before
      merge
