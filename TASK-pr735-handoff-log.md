# TASK pr735-handoff — Log

## 2026-09-23

- User asked: short plain summary, next steps, update documentation and the
  handoff (including remaining findings and next steps), and commit. Created
  this log and the TODO first. The commit request covers one commit; no push
  was requested.
- Found the convention: `TASK-<id>-handoff.md` with a findings table and a
  "What remains" section (e.g. TASK-764). `docs/openapi` covers only partner
  bibliography, and the README has no endpoint list, so no API doc change.
- README Caching section: added a note that `cache.cached` skips the
  responder and its hooks on a cache hit (so `cache_control` is not applied)
  and the `cache.memoize` alternative — found while fixing D3.
- `TASK-pr735-review.md`: added a "Fix status" row and a "Status after
  fixes" section.
- Wrote `TASK-pr735-handoff.md`.
- Pre-commit gates on the final tree: `task format` ✅, `task lint` ✅,
  `task type` ✅, full suite via `task test` ✅ (4443 passed, 2 skipped,
  1 xfailed), coverage of changed modules 100% ✅, flake8 ✅, mypy ✅ (no
  errors in changed files), `task lint-md` ✅.
- `task type-pyright` ❌ exit 123: it lists files from *committed* history,
  which still contains `realia_document_shape.py`, now deleted in the working
  tree. The same pyright 1.1.411 on the actual 13 changed files → 0 errors.
  The gate cannot pass before the commit, so per the instructions I stopped
  before committing and asked the user.
- Asked the user about the `task type-pyright` gate; the user chose "Commit,
  then re-check": one commit (including the staged deletion), then run
  `task type-pyright`, no push. Reworded the handoff so it stays accurate
  once committed.
- Committed `6394de8d` "List only Realia entries the detail route can load"
  (ggshield pre-commit hook passed). No push.
- `task type-pyright` after the commit → 0 errors, exit 0.
- `git ls-remote`: remote branch still `ad222eb3`, local `6394de8d` — the
  commit did not reach GitHub.
- This log entry is written after the commit and is uncommitted.
