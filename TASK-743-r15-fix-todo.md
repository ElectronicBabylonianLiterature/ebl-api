<!-- markdownlint-disable MD013 -->

# TASK-743-r15-fix — TODO

Address R14-1 and the non-blocking findings from `TASK-743-r14-review.md`,
then comment on PR #743 about the two remaining blocking gates.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] TODO + log created before any work (this file + `TASK-743-r15-fix-log.md`)
- [x] Commit made once, on explicit request; not pushed, push, merge, rebase or reset — leave verified changes uncommitted
- [x] No test removed, disabled or skipped without explicit user approval
- [x] No linter / formatter / type-checker configuration file modified
- [x] Every changed `*.py` stays at or under 250 lines
- [x] Every changed source file ends at 100% coverage
- [x] One array never holds two data types

## Steps

- [x] 1. R14-1 — remove the 34 tracked stray files (33 `TASK-*.md` + `TASK-749-frontend.patch`)
- [x] 2. R14-1 — verify `git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'` is empty
- [x] 3. R14-1 — correct "28" to the real count in the PR description
- [x] 4. R14-4 — name the `copilot.instructions.md` change explicitly in the PR description
- [x] 5. R14-6 — make `test_module_facades.py` catch a dropped re-export, not only a dropped definition
- [x] 6. R14-6 — fix any real `__all__` gap the new assertion uncovers
- [x] 7. R14-7 — pin the parser's strict-alternation invariant that the legacy `@pre_load` split relies on
- [x] 8. R14-10 — restore the trailing newline on `ebl/fragmentarium/annotations.json`
- [x] 9. R14-5 — needs explicit approval (deletes tests); ask before touching it
- [x] 10. R14-8 / R14-9 — informational, no action; recorded in the review
- [x] 11. Gates: `task format`, `task lint`, `task type`, `task type-pyright`, `task test`
- [x] 12. Gates: coverage on changed files, `flake8`, `mypy`, `qlty smells --include-tests`, `task lint-md`
- [x] 13. Verify the changed behaviour against the running backend service
- [x] 14. Post a short comment on PR #743 covering R14-2 and R14-3 only
- [x] 15. Report; remind that the r14/r15 task documents still need removing before merge
