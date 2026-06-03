# TASK-717 LOG — Audit devcontainer fix PR

## 2026-06-02

### Started

- Task: Audit PR #717 (fix-devcontainer) on ebl-api
- Also cross-compare with ebl-frontend PR #733
- Fetching PR details, reviews, and comments from GitHub

### Completed (review + plan)

- Fetched PR #717 metadata, diff, reviews (3), and review comments (8 threads)
- Fetched frontend PR #733 diff and architecture for cross-comparison
- Identified 2 BLOCKER findings (F-01 bash/python3 on host; F-02 destructive rebuild)
- Identified 1 MEDIUM finding (F-03 no new-key sync)
- Identified 2 LOW findings (unresolved threads already fixed in code)
- Wrote full review to TASK-717-review.md
- Wrote detailed implementation plan to TASK-717-plan.md

### Blockers preventing merge

1. F-01: `initializeCommand` requires bash + python3 on host (Windows incompatible)
2. F-02: Injection clobbers user-edited `.env` values on every rebuild
3. Fabdulla1 CHANGES_REQUESTED review is active and unresolved

### Plan summary

- Delete `init.sh`; inline file-copy as array `initializeCommand`
- Create `inject-secrets.py` (container-side; clobber guard + new-key sync)
- Extend `postCreateCommand` to call `inject-secrets.py`
- Update docs in `.devcontainer/README.md` and `README.md`
- `TASK-2-todo.md` / `TASK-2-log.md`: already absent from working
  tree — no action needed

### Implementation complete (2026-06-02)

- Deleted `.devcontainer/init.sh`
- Created `.devcontainer/inject-secrets.py` (clobber guard + new-key sync)
- Edited `.devcontainer/devcontainer.json`:
  - `initializeCommand` → array form `["sh", "-c", "test -f .env || ..."]`
  - `postCreateCommand` → extended to call `inject-secrets.py`
- Updated `.devcontainer/README.md`: two-phase lifecycle docs
- Updated `README.md`: removed `init.sh` references, corrected timing
- `task lint-md` \u2014 **0 errors** \u2705
- `inject-secrets.py` manual run \u2014 injected 5 keys successfully \u2705

### Pending

- Manual end-to-end devcontainer test (rebuild + verify injection/guard/sync)
- Mark GitHub threads F-04 and F-05 as resolved
- Commit and push (awaiting explicit user approval)
