# TASK-717 TODO — Audit devcontainer fix PR

## Status: Plan ready — awaiting implementation approval

### Review

- [x] Fetch backend PR #717 details, diff, reviews, and comments
- [x] Fetch frontend PR #733 details and diff for comparison
- [x] Audit backend PR changes for correctness, security, and best practices
- [x] Cross-compare backend and frontend PRs for consistency gaps
- [x] Write detailed review to `TASK-717-review.md`
- [x] Write detailed implementation plan to `TASK-717-plan.md`

### Implementation (complete)

- [x] Delete `.devcontainer/init.sh`
- [x] Create `.devcontainer/inject-secrets.py` (clobber guard + new-key sync)
- [x] Edit `.devcontainer/devcontainer.json` — array `initializeCommand`,
  extend `postCreateCommand`
- [x] Edit `.devcontainer/README.md` — two-phase lifecycle docs, remove
  Windows host-prereq caveat
- [x] Edit `README.md` — fix `init.sh` references, correct injection timing
- [x] Run `task lint-md` — 0 errors ✅
- [ ] Manual devcontainer test (injection, new-key sync, clobber guard)
- [ ] Mark resolved GitHub threads (F-04, F-05)
- [ ] Commit and push (only after explicit user approval)

### Cleanup (before merge)

- [ ] Remove `TASK-717-todo.md`, `TASK-717-log.md`, `TASK-717-review.md`, `TASK-717-plan.md`
