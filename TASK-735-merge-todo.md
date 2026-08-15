# TASK-735-merge TODO — Commit, merge master, finish remaining findings

Branch: `add-realia-slugs-endpoint` → `master`
PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735>

User instruction: commit all changes, merge master into the branch, then
address all remaining findings. No further commits without an explicit
request.

## Steps

- [ ] 1. Create this TODO and `TASK-735-merge-log.md` before any action
- [ ] 2. Pre-commit gate 1 — `task format`
- [ ] 3. Pre-commit gate 2 — `task lint`
- [ ] 4. Pre-commit gate 3 — `task type` (pyre; the gate CI enforces)
- [ ] 5. Pre-commit gate 4 — `task type-pyright`
- [ ] 6. Pre-commit gate 5 — `task test` (full suite)
- [ ] 7. Pre-commit gate 6 — pytest `--cov` on changed modules, 100%
- [ ] 8. Pre-commit gate 7 — `flake8 --max-line-length=120`
- [ ] 9. Pre-commit gate 8 — `mypy --ignore-missing-imports`
- [ ] 10. `task lint-md` for the markdown changes
- [ ] 11. Commit (authorised once, for these changes only)
- [ ] 12. Check whether the commit reached the remote without a push
- [ ] 13. Merge `master` into the branch
- [ ] 14. Re-run every gate after the merge — the merge changes the tree,
       so the pre-merge run is void
- [ ] 15. Re-verify by running the service and exercising `/realia/all`
       against the post-merge tree
- [ ] 16. Finding 4 — update the PR title and description
- [ ] 17. Finding 6 — record the `$expr` full-scan trade-off in the PR body
- [ ] 18. Finding 5 — re-raise; needs a domain answer, cannot be decided here
- [ ] 19. Update `TASK-735-review.md` with final status
- [ ] 20. Re-read copilot instructions; confirm every gate; report results
- [ ] 21. Remind to remove all TASK-735-*.md files before merge
- [ ] 22. Make NO further commits

## Notes

- `task type-pyright` derives its file list from committed history, so it
  cannot run against the uncommitted rename of `test_realia_ids_route.py`.
  Pyright must be run directly pre-commit, and via the task post-commit.
- Commits in this repo have previously reached the remote without an
  explicit push — verify with `git ls-remote` rather than assuming.
