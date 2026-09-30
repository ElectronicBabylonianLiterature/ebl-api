# TASK pr735-merge — TODO

Request: summarise; update documentation and handoff (remaining findings,
next steps); commit once; then merge `master` into the branch.

- [x] Update handoff (`TASK-pr735-fixes-log.md`/`-todo.md`, review
  resolution): remaining findings, next steps, GitHub drafts saved in-repo
- [ ] Prove code unchanged since the green gate runs (re-use code gates)
- [ ] Docs changed → `task lint-md` only
- [ ] Commit (the one commit authorised); verify it was not auto-pushed
- [ ] `git fetch`; merge `origin/master` (authorised); resolve conflicts
- [ ] Merge changes code → run every code gate on the merged tree
- [ ] Runtime re-verify on the merged tree (local Mongo only)
- [ ] Log results; do not push; report
