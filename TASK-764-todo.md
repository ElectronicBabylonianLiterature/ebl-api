# TASK-764 TODO — Review PR #764 "Add the nameParts/nameBreaks migration"

Status legend: `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-todo.md`
- [x] Create `TASK-764-log.md`
- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting
      complete

## 1. Gather PR context

- [x] `gh pr view 764` — metadata, state, mergeability
- [x] Fetch full diff / changed file list
- [x] Fetch commits on the branch
- [x] Identify any branches merged into this one; fetch their feedback too

## 2. Fetch ALL existing feedback (hard gate, non-negotiable)

- [x] `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/764/reviews`
- [x] `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/764/comments`
      (inline/diff)
- [x] `gh api repos/ElectronicBabylonianLiterature/ebl-api/issues/764/comments`
      (conversation)
- [x] Sourcery-AI feedback specifically
- [x] qlty findings
- [x] CodeQL alerts / code-scanning results
- [x] Any other bot reviewers (Codex, Copilot, etc.)
- [x] Human reviewer feedback
- [x] Every unresolved finding explicitly addressed or acknowledged with
      rationale in the review file

## 3. Failing checks

- [x] `gh pr checks 764` — list all checks and statuses
- [x] Pull logs for any failing/blocking check
- [x] Explain root cause of each failure in the review

## 4. Code review of the diff

- [x] Correctness / regressions
- [x] Security
- [x] Test coverage of changed lines (100% required)
- [x] HARD GATE: mixed-type arrays — any array holding >1 data type, id lists
      especially
- [x] HARD GATE: type discriminated by probing an optional field
- [x] HARD GATE: shape split in domain but merged on the wire (or reverse)
- [x] HARD GATE: invariants over shared id space enforced across union of
      separated arrays
- [x] HARD GATE: no `*.py` file over 250 lines
- [x] Type hints present, no unnecessary `Any`
- [x] Full names, small focused functions, no unrequested comments
- [x] Existing style/conventions followed
- [x] No lint/format config modified
- [x] No tests removed/skipped/disabled

## 5. User-specified checks

- [x] Dev container configuration changes — if ANY, warn prominently and check
      very carefully
- [x] No new `.md` files present in the PR
- [x] Never refer to `khoidt` in the third person (it is the user's own account)

## 6. Local verification (hard gate: run the service, not tests alone)

- [x] `task format` (check only — do not leave stray changes)
- [x] `task lint`
- [x] `task type` (pyre — the CI gate)
- [x] `task type-pyright`
- [x] `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] `poetry run flake8 <changed modules> --max-line-length=120`
- [x] `task test` / targeted tests for changed modules
- [x] Coverage on changed modules with `--cov-report=term-missing`
- [x] Run the migration against a LOCAL mongo (127.0.0.1:27017) — never `.env`
      (production URI)
- [x] `task lint-md` for the review markdown

## 7. Write the review

- [x] `TASK-764-review.md`
- [x] Metadata header (date, PR, branch, reviewer, commit reviewed, verdict)
- [x] Short friendly human-looking summary section at the very beginning
- [x] `Details` subsection listing all findings with full details
- [x] Required sections: `Summary`, `Findings`, `Severity`, `Reproduction
      Steps`, `Recommendation`
- [x] Line-length limit disabled in the document so it posts cleanly
- [x] Remind to remove TASK-764-*.md files before merge

## 8. Close out

- [x] Report gates run + results
- [x] Do NOT commit or push anything (no approval given)
