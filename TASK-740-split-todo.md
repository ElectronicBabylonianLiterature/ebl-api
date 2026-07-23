# TASK-740 Split — TODO

Split the work currently in the `add-realia-annotation-api` working tree.
Everything not directly related to the realia annotation API moves to a
new branch off `master` and gets its own PR.

## Classification

Group A stays on `add-realia-annotation-api` (uncommitted, as now).
Group B moves to the new branch.

- [x] Diff every changed file against `HEAD` and classify hunk by hunk
- [x] Confirm no file needs splitting across both groups, or handle it

## Group B — the new branch

- [x] Grammar directory rename `lark_parser/` -> `atf_grammar/` and its
      8 references
- [x] mypy fixes that the rename surfaced in `lark_parser.py`,
      `legacy_atf_converter.py`, `legacy_atf_line_validator.py`,
      `lark_parser_errors.py`
- [~] Pre-existing mypy fixes — `text_line.py` and `word_tokens.py`
      moved; `fragment.py`, `fragment_updater.py`, `fragments.py` and
      `scopes.py` stayed with #740, see the log for why
- [x] pyright fixes and their tests (`test_atf_preprocessor.py`,
      `test_start_parser.py`, `test_atf_parser.py`,
      `test_fragment_repository_updates.py` WordId hunk)
- [~] E203 slice fix — stayed with #740 with the rest of `fragment.py`
- [x] `docs/ebl-atf.md` link update

## Execution

- [x] Snapshot the full working tree so nothing can be lost
- [x] Create a worktree on a new branch off `master`
- [x] Apply Group B there — copy whole files only where `master` matches
      the current branch, otherwise re-apply the hunk by hand
- [x] Revert Group B from the `add-realia-annotation-api` working tree
- [x] Verify Group A still passes its gates
- [x] Verify Group B passes its gates on the new branch
- [x] Commit and push the new branch; opened PR #743
- [x] Leave Group A uncommitted — not authorised to commit it

## Gates on the new branch before the PR

- [x] `task format`
- [x] `task lint`
- [~] `task type` (pyre) — crashes in this environment, flagged in
      the PR body for CI to confirm
- [~] pyright — 9 factory_boy stub errors remain, documented in the PR
- [x] `task test` — 3842 passed, 2 skipped, 1 xfailed
- [x] `task lint-md`
- [x] `flake8 --max-line-length=120`
- [x] `mypy --ignore-missing-imports`
- [x] Every changed `*.py` under 250 lines
- [x] Run the modified service and exercise an affected route
