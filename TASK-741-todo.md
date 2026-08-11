# TASK-741 TODO — Review PR #741

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>
Branch: `fix-afo-register-texts-numbers-split` → `master`

## Steps

- [x] Fetch PR metadata, commits, diff
- [x] Fetch submitted reviews (`/pulls/741/reviews`) — 2 found
- [x] Fetch inline diff comments (`/pulls/741/comments`) — none exist
- [x] Fetch issue/conversation comments (`/issues/741/comments`) — 1 found
- [x] Fetch review-thread resolution state (GraphQL) — 0 threads
- [x] Identify merged-in branches/PRs — only `origin/master`, no PR feedback
- [x] Check CI check runs / statuses — all pass; Sourcery re-review skipped
- [x] Check qlty findings — no blocking issues, coverage diff 100%
- [x] Read full diff and analyse correctness, regressions, security, coverage
- [x] Verify behaviour locally (falcon test client + in-memory MongoDB)
- [x] Verify hard gates on changed files: 250-line cap, coverage, flake8, mypy
- [x] Write `TASK-741-review.md` with the required template sections
- [x] Address/acknowledge every unresolved finding in the review file
- [x] Run `task lint-md` — 0 errors
- [ ] Remind to remove task-tracking `.md` files before merge (done in review;
      files still present in the working tree)

## Addressing the findings

- [x] Finding 1 — restore `.gitignore` and `test_retrieve_annotations.py` to
      the `origin/master` versions
- [x] Finding 2 — add `MAX_QUERY_TOKENS` (web) and `MAX_CANDIDATES` (repo)
      bounds, verify the 500 becomes a 422
- [x] Finding 3 — restore the `isinstance(query, str)` guard
- [x] Finding 4 — stop interpolating the request body into the 404 message
- [x] Finding 10 — extract `test_afo_register_candidate_query.py`
- [x] Tests for every new limit, 100% coverage on changed modules
- [x] Gates: `task format`, `task lint`, `task lint-md`, flake8, mypy,
      `task type` (pyre), pyright (master's `type-pyright` command, absent
      from this branch), 250-line cap
- [x] `task test` (full suite) — 3868 passed, 2 skipped, 1 xfailed, exit 0
- [x] Commit — `5b716e5b`, code files only (user-requested)
- [x] Merge `origin/master` — merge commit `7fc44160`, no conflicts
- [x] Re-run every gate on the merged tree — all pass
- [x] Push — happened without `git push` being run; PR is now `MERGEABLE`
- [x] Commit the task docs, then remove them and commit again (user-requested)
- [x] Confirm no other task docs exist — `find` for `TASK-*.md` returns only
      the three `TASK-741-*` files; the `TASK-743-docs-cleanup-*` files
      referenced earlier never existed
- [ ] Finding 5 — re-request review, `@sourcery-ai review` — needs approval
- [ ] Finding 7 — confirm frontend batch sizes (different repository)
