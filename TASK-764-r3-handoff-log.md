<!-- markdownlint-disable MD013 -->

# TASK-764-r3-handoff — Work Log

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Checked `git ls-files` for both file names before creating them.
- Created this log and `TASK-764-r3-handoff-todo.md` before starting.
- Scope: refresh docs and handoff, then one commit of the already-gated #764
  work. No push requested.

### Work

- Checked `docs/`: neither `docs/ebl-atf.md` nor `docs/openapi` mentions
  `nameParts`, so no repository documentation needed updating for this change.
  The migration documents itself in its module docstring and in #764's body.
- Wrote `TASK-CURRENT-handoff.md`, one document covering both PRs, superseding
  `TASK-743-r15-handoff.md`. It carries every remaining finding with an owner
  and a next step, the deployment ordering, and a merge checklist.

### Errors and recoveries

- The first full-suite run reported exit 1 and was flagged as a failure. It was
  not a test failure: the scratch directory had been cleaned out from under the
  output redirect, so pytest never started. Checked rather than assuming a
  regression, recreated the directory and re-ran: 4556 passed.
- `task lint-md` twice rejected the handoff because a wrapped line began with
  `#764`, which markdownlint reads as an ATX heading. Reflowing did not help,
  since the wrap point moved. Fixed by prefixing any line that opens with a PR
  reference, so no line starts with `#`.

### Gates before the commit, run in order

| | |
| --- | --- |
| 1 `task format` | 830 files already formatted |
| 2 `task lint` | All checks passed |
| 3 `task type` (pyre) | **No type errors found** |
| 4 pyright | 0 errors, 0 warnings, 0 informations |
| 5 `pytest` | 4556 passed, 2 skipped, 1 xfailed, 0 failed |
| 6 coverage | `migrate_name_breaks.py` 100%, nothing missing |
| 7 flake8 | 0 |
| 8 mypy | no issues |
| 9 qlty `--include-tests` | no findings |
| `task lint-md` | 0 errors |

### Commit

- `d83582a2` "Remove the task documents and match the migration to the repo's
  typing style". One commit, on explicit request.
- **Not pushed.** The remote is still at `31929977`; confirmed with
  `git ls-remote`, because a commit reached GitHub without a push earlier in
  this project's history.
- `git diff --diff-filter=A --name-only -M origin/master...HEAD` filtered to
  non-`ebl/` paths now returns **0** on this branch.
- No task document was committed. All of them remain untracked by design.
