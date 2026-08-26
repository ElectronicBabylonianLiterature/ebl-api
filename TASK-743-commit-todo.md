# TASK-743-commit — Commit the review fixes — TODO

Task: commit the working-tree changes. The user asked for this explicitly in
their own words ("Please commit all the changes"). Single-use authorisation:
it covers exactly one commit of exactly these changes, and does NOT authorise
a push.

## Checklist

- [ ] 1. Create task TODO + log (this file, `TASK-743-commit-log.md`)
- [ ] 2. Record the pre-commit remote SHA (`git ls-remote`) so an auto-push
      can be detected afterwards
- [ ] 3. Confirm what goes in the commit — ASK about the TASK-743*.md
      tracking docs, which my own review flagged as "no new .md files"
- [ ] 4. Pre-commit gate 1 — `task format` (exit 0, no unstaged changes left)
- [ ] 5. Pre-commit gate 2 — `task lint` (ruff)
- [ ] 6. Pre-commit gate 3 — `task type` (pyre, the CI gate)
- [ ] 7. Pre-commit gate 4 — `task type-pyright`
- [ ] 8. Pre-commit gate 5 — `task test` (full suite)
- [ ] 9. Pre-commit gate 6 — coverage on changed modules
- [ ] 10. Pre-commit gate 7 — `flake8 --max-line-length=120`
- [ ] 11. Pre-commit gate 8 — `mypy --ignore-missing-imports`
- [ ] 12. `task lint-md` (markdown changed)
- [ ] 13. 250-line limit on every changed file
- [ ] 14. Stage and commit with a descriptive message
- [ ] 15. Verify against `git ls-remote` whether the commit reached the remote
      and report honestly either way
- [ ] 16. Re-read copilot instructions; report which gates ran and results
