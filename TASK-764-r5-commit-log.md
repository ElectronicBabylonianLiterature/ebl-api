# TASK-764-r5-commit — Work Log

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Checked `git ls-files` for both names first.
- Created this log and `TASK-764-r5-commit-todo.md` before starting.
- Scope: commit the 16 modified documents plus `TASK-743-r15-handoff.md`, which
  needs the change re-applied. No push requested.

<!-- markdownlint-configure-file { "MD013": false } -->

### Frontend check — `ebl-frontend` e281f7ba

Verified rather than taken from the commit message:

- `gh api .../compare/master...e281f7ba` returns **status=identical**, so the
  commit *is* `ebl-frontend` master. PR #817, merged 2026-09-16.
- Read `nameTokens()` in `src/transliteration/domain/token.ts` at that sha. It
  destructures `nameParts` and `nameBreaks`, and **returns `nameParts` untouched
  when `nameBreaks` is falsy**, otherwise `_.zip(...).flatMap(...)`. Both call
  sites that walk a name, `extractEnclosureTypes` and `addAccents`, go through it.
- `nameBreaks: []` is truthy in JS and takes the zip path, which yields the parts
  unchanged — so the empty case is right as well, not an accident.

**What it does and does not solve.** It closes R14-2 and it removes the
frontend/backend lock-step, because the new frontend renders the old shape. It
does **not** touch the remaining ordering, which is backend-to-database: the
migration writes `nameBreaks` into stored documents and an API without #743's
schema raises on the unknown field when loading them. `migrate_name_breaks.py`
says so in its own docstring. #743 must be deployed before `--apply` runs,
frontend or no frontend.

With R14-1 and R14-3 already closed, **#743 now has no blocking findings.**

### Documentation updated before committing

- `TASK-CURRENT-handoff.md` — R14-2 closed with the evidence; the ordering
  section rewritten around the backend-to-database constraint; merge checklist
  ticked for the frontend merge and both pushes, with a new unticked item for
  the frontend *deployment*, which merging does not imply.
- `TASK-743-r14-review.md` — R14-2 marked closed in the findings table and in its
  detail section; a dated status line added to the metadata header recording that
  all three blocking findings are now closed.

### Gates before the commit

No `*.py` changed since `18f386a0`, and the gates were run in order regardless:
`task format` 830 files formatted · `task lint` clean · `task type` (pyre)
no type errors · `task type-pyright` 0/0/0 · full suite **4556 passed, 2 skipped,
1 xfailed** · `task lint-md` 0 errors across 23 files.

<!-- markdownlint-configure-file { "MD013": false } -->
