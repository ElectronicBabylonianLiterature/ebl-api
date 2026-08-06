# TASK-743-merge — TODO

Merge `master` into `fix-type-checker-blind-spots` (PR #743) and resolve
all merge conflicts.

## Checklist

- [x] Fetch `origin` and fast-forward local `master` to `origin/master`
- [x] Record pre-merge state (branch head, master head, dirty files)
- [x] Run `git merge master` and capture the conflict list
- [x] Resolve every conflicted file, preserving both sides' intent
- [x] Re-read `.github/instructions/copilot.instructions.md` — `master` had
      rewritten it substantially
- [x] Verify the 250-line hard gate on every `.py` file touched by the merge
- [x] Gate 1: `task format` — PASS, exit 0, nothing left unstaged
- [x] Gate 2: `task lint` (ruff) — PASS
- [x] Gate 3: `task type` (pyre, CI-enforced) — PASS, no type errors
- [x] Gate 4: `task type-pyright` — PASS, 0 errors / 0 warnings
- [x] Gate 5: `task test` — PASS, 4245 passed, 0 failures
- [x] Gate 6: coverage on changed modules — PASS, 521 stmts, 0 missed, 100%
- [x] Gate 7: `flake8 --max-line-length=120` — 1 error, pre-existing on
      master, not introduced here
- [x] Gate 8: `mypy --ignore-missing-imports` — 42 errors, all pre-existing on
      master; zero in any branch-touched file
- [x] `task lint-md` — PASS, 0 errors
- [x] Runtime verification: merged app booted, ATF route returned 200
- [x] Report results and **ask for explicit approval before committing**
- [ ] **Merge commit NOT created** — awaiting explicit user approval
- [ ] Remind to delete `TASK-743-merge-todo.md` and `TASK-743-merge-log.md`
      before the PR is merged

## Open questions for the user

- [ ] Uncommitted edit in `docs/ebl-atf.md` corrupts a sentence
      (`defined i[ebl-atf.lark]`). Not authored by this task. It was stashed
      to unblock the merge (`stash@{0}`), not discarded. Restore it, fix the
      typo, or drop it?
- [ ] Pre-existing master debt inherited by the merge — 1 flake8 E501 in
      `museum.py`, 42 mypy errors, 3 files over 250 lines. Left untouched so
      the merge commit stays a pure merge. Fix separately?
