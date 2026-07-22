# TASK-740 TODO

Address Fabdulla1's CHANGES_REQUESTED review on PR #740.

Chosen approach: **Both** — graceful degradation plus full test coverage.

- [x] Fetch all PR feedback (reviews, inline comments, issue comments, bots).
- [x] Catch `PyMongoError` in `resolve_realia_info` and
  `resolve_realia_info_map` so a post-write realia lookup failure degrades
  to empty `realiaInfo` instead of an ambiguous 500. (Concern 1)
- [x] Unit tests: both resolvers degrade to empty on infrastructure failure.
- [x] Route tests (Concern 2): infrastructure failure yields HTTP 200 with
  empty `realiaInfo` on the read, retrieve-all, and post-write paths.
- [x] Pre-commit gates: `task format`, `task test`, per-module coverage,
  `flake8`, `mypy`, `task type` (pyre), `task lint-md`.
- [ ] Remind to remove TASK-740 docs before the PR is merged.
