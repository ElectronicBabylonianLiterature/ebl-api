# TASK pr735-rereview — Log

## 2026-09-23

- Created TODO and log before any review work.
- Read copilot instructions in full.
- PR #735 head is `6394de8d` (matches `origin/add-realia-slugs-endpoint`); 22
  files, +1277 / −7. Previous review covered `ad222eb3`.
- Fetched reviews (7), inline comments (4), issue comments (1), commits (17),
  files (22) via `gh api --paginate`; saved in the scratchpad.
- Feedback: Sourcery approved `6394de8d`; Fabdulla1's last review (2026-08-18,
  `ad222eb3`) is CHANGES_REQUESTED. Both Fabdulla1 inline threads (bootstrap.py
  collision, stub filter `$isArray`) are unresolved with no reply. No reply to
  the 2026-08-18 review body either. No pending review requests.
- No other PR is merged into this branch except `origin/master` (merge commit
  `0f37a27f`), so there is no extra PR feedback to fetch.
- CI on `6394de8d`: all checks pass (tests 3.11/3.12/pypy-3.11 on both runs,
  CodeQL "No new alerts", GitGuardian, Sourcery, qlty check "No blocking
  issues", qlty coverage diff 100%). `docker` skipped (normal for PRs). The
  code-scanning alerts API returned 403 for this token; used the CodeQL
  check-run summary instead.
- Dev container / config: net diff touches none of `.devcontainer`, `.github`,
  `.claude`, Taskfile, pyproject, lock, ini, yml, Dockerfile, compose. No
  warning needed.
- **New `.md` files: 8 `TASK-pr735-*.md` files (+601 lines) were added by head
  commit `6394de8d`.** Blocking finding.
- PR body was updated by the publish task and matches the code.
- Read the whole source and test diff. All changed `.py` files are 189 lines or
  fewer. No comments, type hints present, data hard gate not affected (one array
  of string IDs).
- Local gates on `6394de8d` (working tree differs only in TASK files):
  - `task format` exit 0 (811 files already formatted, no changes);
    `task lint` exit 0; `task type` (pyre) no errors; `task type-pyright`
    0 errors; flake8 on changed `.py` exit 0.
  - mypy on changed `.py`: 0 errors in changed files; 26 errors in 17
    untouched, transitively imported modules (pre-existing on master).
  - Coverage of changed source modules: 100% (193 statements, 188 tests).
    Changed test files measured with a scratch coveragerc: new files 100%;
    `test_realia_info.py` lines 26–35 uncovered, from master commit
    `a238304d`, not touched by the PR.
  - `task lint-md`: **error I made** — my new TODO/log had lines over 80
    chars (MD013). Rewrapped them; lint-md on them now reports 0 errors. All
    other `.md` files report 0 errors.
- Runtime (local mongod `127.0.0.1:27017`, throwaway DB `ebl_review_pr735b`,
  never `.env`; serve scripts reused from the fixes session):
  - Null cache, port 8736: `GET /realia/all` → 200, `Cache-Control: public,
    max-age=600`, 10 IDs; `Pig`, `all`, `NullType`, `NullRealiaId`,
    `BadElement`, `42` excluded. Every listed ID (incl. `""`, `by-id`,
    `"trail "`, `q?x`, `50%`, `h#1`, `a/b`) → 200 from `/realia/{id}` when
    percent-encoded. Only traceback in the log: `/realia/NullType`
    (unlisted, pre-existing detail-route 500).
  - `CACHE_TYPE=simple`, port 8737: 5 GETs → 1 `realia` query (profiler),
    header on every response.
  - Servers stopped (exit 143/144 are my own kills); DB dropped (verified).
- `CACHE_CONFIG` is not set anywhere in the repo; production value is unknown.
- Interrupted: the user declined my read of `TASK-pr735-review.md` before I
  rewrote it, and asked me to address the findings instead (task
  `pr735-address`). The review document has not been rewritten; the full
  test run was cut off at ~60% by the session ending.
