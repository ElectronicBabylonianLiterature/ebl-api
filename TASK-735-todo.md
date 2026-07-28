# TASK-735 TODO — PR #735 (Realia ID listing endpoint)

## Phase 1 — Review (complete)

- [x] Create task TODO and log files
- [x] Fetch PR metadata, commits, and full diff
- [x] Fetch all submitted reviews (`pulls/735/reviews`) — 2 found
- [x] Fetch all inline diff review comments (`pulls/735/comments`) — 2 found
- [x] Fetch all issue/conversation comments (`issues/735/comments`) — 1 found
- [x] Fetch review threads + resolution state (GraphQL) — both resolved
- [x] Check for merged-in branch PRs — none, branch is linear
- [x] Check CI check runs / statuses — all 17 pass, docker skipped
- [x] Check qlty findings — cloud clean; local: 13 B101 + 1 S1192
- [x] Verify behaviour locally: 73 realia tests pass
- [x] Probe behavioural edge cases; probe module removed afterwards
- [x] Write `TASK-735-review.md` with required template sections
- [x] Run `task lint-md` — 0 errors

## Phase 2 — Address findings (complete)

- [x] Confirm decisions on findings 1/4, 3, and 5 with the user
- [x] Finding 1 + 4 — route moved to `/realia/ids`; shadowing test
      replaced by `test_entry_named_all_is_reachable`
- [x] Finding 2 — `relatedTerms` / `type` / `wikidataId` now count as own
      content, one parametrised test per field
- [x] Finding 3 — dropped `PLACEHOLDER_REALLEXIKON_COUNT`; reallexikon
      counts only when a reference resolves
- [x] Finding 5 — accent- and case-insensitive sort key, IDs returned
      verbatim, tie-break on the original string
- [x] Finding 6 — `cache_control(["public", "max-age=600"])` on the
      list resource, asserted in a route test
- [x] Finding 7 — `"$ifNull"` extracted as `IF_NULL` (qlty S1192 gone)
- [x] Finding 8 — listing tests split into `test_realia_list_ids.py` and
      `test_realia_ids_route.py`; largest changed file now 198 lines
- [x] Gitignore `.claude/`, `CLAUDE.md`, `CLAUDE.local.md`, `.qlty/`
- [x] `task format` — 733 files formatted, no diff
- [x] `task lint` (ruff) — all checks passed
- [x] `task test` — 3808 passed, 2 skipped, 1 xfailed
- [x] Coverage on `ebl/realia` — 100%, 0 missing
- [x] `flake8 --max-line-length=120` — clean
- [x] `mypy` — 0 errors in changed files
- [x] `task type` (pyre) — no type errors
- [x] `qlty check --upstream=master` — only `bandit:B101` in tests
- [x] `task lint-md` — 0 errors
- [x] Update `TASK-735-review.md` with the resolution of each finding

## Phase 3 — Pylance gate and frontend prompt (complete)

- [x] Run pyright/Pylance on the changed files — 5 errors found, all
      pre-existing on `master` but inside files this PR touches
- [x] Fix `_load_entry` and `search` schema-load types with `cast`,
      matching the pattern in `mongo_sign_repository.py`
- [x] Fix `RealiaSearchResource` `get_param` optionality
- [x] Re-run pyright on all 10 changed files — 0 errors
- [x] Re-run `task format`, `task lint`, flake8, mypy, `task type`,
      `task test`, coverage, qlty, `task lint-md` after the edits
- [x] Write `TASK-735-frontend-prompt.md`

## Phase 4 — Hard-gate pyright (complete)

- [x] Establish why the gate was skipped (instructions list, a false
      memory, dismissed IDE diagnostics)
- [x] Add `type-pyright` task to `Taskfile.dist.yml`, pinned to
      `pyright@1.1.411`, scoped to changed + untracked Python files
- [x] Fix the task's first version, which silently skipped new files
- [x] Add `type-pyright` to `task test-all`
- [x] Verify the gate passes on clean files and fails on dirty ones
- [x] Add `task type` and `task type-pyright` to the documented
      pre-commit hard gates in the copilot instructions
- [x] Correct the project memory that caused the miss
- [x] `task lint-md` — 0 errors
- [ ] Commit the changes (awaiting user go-ahead)
- [ ] Remove task artifacts before merge (user action)

## Outcome

All eight findings resolved and the changed files are clean under all
three type checkers. Two contract changes to communicate: endpoint path
`/realia/all` -> `/realia/ids`, and response ordering is now accent- and
case-insensitive.

Out of scope and left alone: 102 pre-existing pyright errors in
`realia_schemas.py`, `test_realia_cross_references.py`, and
`test_realia_entry.py` — none of these files is touched by this PR.
