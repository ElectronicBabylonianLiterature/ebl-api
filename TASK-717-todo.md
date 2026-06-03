# TASK-717 TODO — Audit devcontainer fix PR

## Status: Implementation round 2 complete — awaiting commit approval

### Review round 1 (complete)

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
- [x] Manual devcontainer test (rebuild + verify sync-env.py runs,
  all keys present after container start)
- [x] Mark resolved GitHub threads (F-04, F-05, F-01/host-bash,
  CodeQL) — all 4 unresolved threads resolved ✅
- [ ] Commit and push (only after explicit user approval)

### Review round 2 (complete)

- [x] Re-fetch all PR #717 reviews and comments from GitHub
- [x] Re-fetch frontend PR #733 diff for updated cross-comparison
- [x] Audit current branch state for correctness, security, and
  naming consistency
- [x] New finding F-06: rename to `sync-env.py` and update all references
- [x] New finding F-07: clarify `.env` runtime role and Codespaces
  override mechanism in README
- [x] Update `TASK-717-review.md` with round 2 findings

### Implementation round 2 (complete)

- [x] Rename `.devcontainer/inject-secrets.py` → `sync-env.py`
- [x] Update `postCreateCommand` in `devcontainer.json`
- [x] Update references in `.devcontainer/README.md`
- [x] Update references in `README.md`
- [x] Clarify `.env` and Codespaces override behaviour in
  `.devcontainer/README.md` ("How it works" subsection added)
- [x] Write tests for `sync-env.py` — 13 tests, 100% coverage ✅
- [x] Run `task lint-md` — 0 errors ✅
- [ ] `git pull` to sync with remote (branch is 1 commit behind)
- [ ] Commit and push (only after explicit user approval)

### Security remediation (complete)

- [x] Redesign `inject-secrets.py`: removed secret-to-disk write;
  now only appends missing placeholder keys
- [x] Update `.devcontainer/README.md` to document Codespaces native
  injection and revised script scope
- [x] Run `task lint-md` — 0 errors ✅
- [x] Commit and push ✅ (committed in f9b601f, pushed)

### Cleanup (before merge)

- [ ] Remove `TASK-717-todo.md`, `TASK-717-log.md`, `TASK-717-review.md`, `TASK-717-plan.md`
