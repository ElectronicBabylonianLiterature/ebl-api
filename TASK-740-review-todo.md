# TASK-740 Review — TODO

Review of PR #740 "Realia annotation API: resolve realiaInfo on every
fragment-returning route" (`add-realia-annotation-api` to `master`).

## Steps

- [x] Create TODO and log files (this file + `TASK-740-review-log.md`)
- [x] Fetch PR metadata, description, commits, files changed
- [x] Fetch all submitted reviews (`/pulls/740/reviews`)
- [x] Fetch all inline diff comments (`/pulls/740/comments`)
- [x] Fetch all issue/conversation comments (`/issues/740/comments`) —
      none exist
- [x] Fetch bot feedback specifically (Sourcery, qlty, Codex)
- [x] Identify any PRs merged into this branch — only `origin/master`
- [x] Fetch CI check runs; identify failing tests
- [x] Investigate every failing test — root cause found and reproduced
- [x] Read the full diff against `master`
- [x] Check data hard gate: one array = one data type at domain / Mongo /
      wire — passes
- [x] Check shared-id-space invariants across the union of split arrays —
      enforced, verified live
- [x] Check 250-line limit on every touched `*.py` file — all pass
- [x] Check type hints, `Any` usage, function size, naming
- [x] Run gates: `task format`, `task lint`, `task type` (pyre),
      `task type-pyright`, `task test`, `task lint-md`
- [x] Run coverage on changed modules — 100% on all touched lines
- [x] Run `flake8 --max-line-length=120` and
      `mypy --ignore-missing-imports` on changed modules
- [x] Run the modified backend service and exercise affected routes —
      found the 500 in finding 2
- [x] Address or explicitly acknowledge every unresolved finding from
      existing PR feedback
- [x] Write `TASK-740-review.md` with Summary / Findings / Severity /
      Reproduction Steps / Recommendation
- [x] Re-read copilot instructions; confirm every gate honoured; report
- [ ] Remove TASK-740 tracking files before the PR is merged (reminder
      issued to the user; the PR head also still carries
      `TASK-740-todo.md` and `TASK-740-log.md`)
