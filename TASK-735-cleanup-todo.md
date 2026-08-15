# TASK-735-cleanup TODO — Commit the alignment, then remove PR docs

User instruction: commit all changes, then remove all the PR docs and
commit again. Two commits authorised, both single-use.

## Steps

- [ ] 1. Create this TODO and `TASK-735-cleanup-log.md` first
- [ ] 2. Pre-commit gate 1 — `task format`
- [ ] 3. Pre-commit gate 2 — `task lint`
- [ ] 4. Pre-commit gate 3 — `task type` (pyre)
- [ ] 5. Pre-commit gate 4 — `task type-pyright`
- [ ] 6. Pre-commit gate 5 — `task test` (full suite)
- [ ] 7. Pre-commit gate 6 — coverage 100% on changed modules
- [ ] 8. Pre-commit gate 7 — `flake8 --max-line-length=120`
- [ ] 9. Pre-commit gate 8 — `mypy --ignore-missing-imports`
- [ ] 10. `task lint-md`
- [ ] 11. Commit 1 — the rule alignment and the merge fix
- [ ] 12. Verify whether commit 1 reached the remote without a push
- [ ] 13. Remove every `TASK-735-*.md` file
- [ ] 14. Re-run all gates before commit 2 — the tree changed
- [ ] 15. Commit 2 — removal of the PR docs
- [ ] 16. Verify final state; confirm nothing was pushed
- [ ] 17. Report

## Notes

- Both commit authorisations are single-use and do not carry forward.
- No push was requested; do not push.
- This TODO and its log are themselves PR docs and are removed by step 13.
