# TASK-744 TODO — Frontend PR for the `nameBreaks` split

<!-- markdownlint-disable MD013 -->

Task: create a pull request in `ElectronicBabylonianLiterature/ebl-frontend`
implementing the client side of the `nameParts` / `nameBreaks` split, which is
blocking gate 1 on ebl-api PR #743.

Status legend: `[ ]` pending, `[~]` in progress, `[x]` done, `[!]` blocked

## 0. Task artefacts (hard gate)

- [x] Create `TASK-744-todo.md` before starting work
- [x] Create `TASK-744-log.md` before starting work
- [ ] Keep both updated as each step completes
- [ ] Remind user to remove the task files before the PR is merged

## 1. Scope and confirm

- [ ] Clone `ebl-frontend` and confirm its default branch
- [ ] Find every place the client reads `nameParts`
- [ ] Confirm with the user what "and the migration script" means for a
      frontend PR — the migration is backend Python and is already committed
      to ebl-api

## 2. Implement

- [ ] Branch from the frontend default branch
- [ ] Add `nameBreaks` to the token type definitions
- [ ] Interleave `nameParts` and `nameBreaks` wherever a name is rendered
- [ ] Keep reading legacy payloads if the frontend must work against an
      un-deployed backend
- [ ] Update any test fixtures carrying `nameParts`

## 3. Gates (frontend equivalents)

- [ ] Lint
- [ ] Type check
- [ ] Unit tests
- [ ] Coverage on changed files
- [ ] Run the app and confirm a broken name renders with its bracket

## 4. Deliver

- [ ] Ask before committing
- [ ] Ask before pushing
- [ ] Open the PR, cross-linking ebl-api #743 and stating the deploy ordering
- [ ] Report back with the PR URL
