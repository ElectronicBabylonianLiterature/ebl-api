# TASK-743 TODO — Review PR #743 "Make the ATF parser visible to the type checkers"

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743>
Branch: `fix-type-checker-blind-spots` -> `master`

## Setup

- [x] Read `.github/instructions/copilot.instructions.md` in full
- [x] Identify PR number and branch
- [x] Create `TASK-743-todo.md`
- [x] Create `TASK-743-log.md`

## Gather existing feedback (HARD GATE — non-negotiable)

- [x] `gh api .../pulls/743/reviews` — 5 reviews
- [x] `gh api .../pulls/743/comments` — 13 inline diff comments
- [x] `gh api .../issues/743/comments` — 1 conversation comment
- [x] Capture Sourcery AI feedback — 1 issue (`TextLine.merge`)
- [x] Capture qlty findings — 9 inline, 6 currently blocking
- [x] Capture CodeQL / advanced-security feedback — 3 alerts
- [x] Capture human reviewer feedback — Fabdulla1, CHANGES_REQUESTED, 5 points
- [x] Fetch feedback for the related PR #740 this was split out of
- [x] Confirm no feature PR was merged into this branch (master merges only)
- [x] Check CI check runs / statuses — all green

## Review the diff

- [x] Full diff vs `master` (102 files, +4208 / -2992)
- [x] Data hard gate: mixed-type arrays, probing, domain/wire mismatch
- [x] 250-line limit on every touched `*.py`
- [x] Type hints, no unnecessary `Any`, full names, function size
- [x] No disabled/removed tests, no silenced lint rules, no ignore comments
- [x] Grammar-directory rename is a pure rename with no stale references

## Verify locally

- [x] `task format` — clean
- [x] `task lint` — passed
- [x] `task type` (pyre — CI gate) — no errors
- [x] `task type-pyright` — 0 errors
- [x] `task test` — 4366 passed, 2 skipped, 1 xfailed
- [x] `poetry run pytest` with `--cov` on changed modules
- [x] `poetry run flake8 --max-line-length=120` — 0 errors
- [x] `poetry run mypy --ignore-missing-imports` — 0 in changed files
- [x] `task lint-md` — clean
- [x] Run the modified backend service and exercise the affected routes
- [x] Diff `nameParts` wire output master vs branch — byte-identical

## Write the review document

- [x] Create `TASK-743-review.md`
- [x] Friendly, very short, human-looking summary at the very beginning
- [x] `Details` subsection with all findings, line-length limit lifted
- [x] Template sections: `Summary`, `Findings`, `Severity`,
      `Reproduction Steps`, `Recommendation`
- [x] Every existing PR finding explicitly addressed or acknowledged

## Close out

- [x] Re-read copilot instructions and confirm every gate honoured
- [x] Report gates run and their results
- [x] Remind to remove `TASK-743-*.md` before merge
- [x] Do NOT commit or push
