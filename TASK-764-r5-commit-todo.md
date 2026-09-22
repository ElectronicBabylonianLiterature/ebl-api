# TASK-764-r5-commit — TODO

Commit the markdown directive move, at the user's explicit request.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] TODO + log created before any work, names checked against `git ls-files`
- [x] Commit once, on this explicit request; do **not** push
- [x] Pre-commit gates 1-9 run in order and confirmed
- [x] `task lint-md` clean
- [x] No linter or formatter configuration modified

## Steps

- [x] 1. Re-apply the move to `TASK-743-r15-handoff.md`, which the open editor
      reverted, so all 17 documents are consistent
- [x] 2. Confirm no `*.py` changed, then run gates 1-9 in order anyway
- [x] 3. `task lint-md`
- [x] 4. Commit
- [x] 5. Confirm nothing was pushed, and report

<!-- markdownlint-configure-file { "MD013": false } -->
