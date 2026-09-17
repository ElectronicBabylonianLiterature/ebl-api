<!-- markdownlint-disable MD013 -->
# TASK-743-r13-codeql — TODO

Address the findings open after the push of `13b80d92` on PR #743.

New task; own TODO and log, created before work. Does not inherit
`TASK-743-r13-watch-*` or any earlier task's files.

## Gate note

"Address all the findings" is **not** authorization to commit or push. The
previous commit approval was single-use and is spent. The CodeQL fix only clears
the PR once it is committed and pushed, so the work stops at a verified working
tree and I ask.

## Findings to address

- [ ] 1. Create TODO + log
- [ ] 2. **CodeQL: `assert` with a side-effect** in `test_named_sign_errors.py` — already patched in the tree, needs full re-verification
- [ ] 3. Two unreported `assert _status_for(...)` route tests — already patched, same
- [ ] 4. Read the six Test Python job conclusions; address anything they report
- [ ] 5. Re-check every other check and status on the pushed head
- [ ] 6. Confirm no NEW review threads or comments since the push
- [ ] 7. Full gates in order: format, lint, pyre, type-pyright (run directly), test, coverage, flake8, mypy, qlty, lint-md
- [ ] 8. Re-verify at runtime — the previous service run is void after a rewrite
- [ ] 9. Update the review, handoff and logs with what changed
- [ ] 10. Report and **ask** before committing or pushing

## Standing decisions, not to be reopened

- **B1** (now 28+ root artefacts) — deferred to merge time by the user.
- **N5** (stale approval / re-request review) — offered and declined.
- **N6** (#764's 14 artefacts) — another branch.
- **I1** (`manuscript_line.paratext` mixed array) — informational, no action asked.
- **N2 operational** — the production migration dry-run is the user's to run;
  `.env` points at production and must never be sourced here.
