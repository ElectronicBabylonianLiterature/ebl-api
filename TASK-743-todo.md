# TASK-743 TODO — Review PR #743 (Make the ATF parser visible to the type checkers)

Status legend: `[ ]` pending, `[~]` in progress, `[x]` done, `[!]` blocked

## 0. Task artefacts (hard gate)

- [x] Create `TASK-743-todo.md` before starting work
- [x] Create `TASK-743-log.md` before starting work
- [x] Keep both updated as each step completes
- [x] Remind user to remove all three TASK files before the PR is merged

## 1. Gather PR state

- [x] `gh pr view 743` — title, body, base, head, mergeability
- [x] Full diff (`gh pr diff 743`) and changed-file list with line counts
- [x] Commit list on the branch
- [x] Identify any branches merged into this one; fetch their PR feedback too

## 2. Fetch ALL existing feedback (hard gate — review is incomplete without this)

- [x] `gh api repos/<owner>/<repo>/pulls/743/reviews`
- [x] `gh api repos/<owner>/<repo>/pulls/743/comments` (inline diff comments)
- [x] `gh api repos/<owner>/<repo>/issues/743/comments` (conversation comments)
- [x] Include bots: Sourcery AI, qlty, CodeQL, Codex, Copilot, any other agent
- [x] Record every unresolved finding; each must be addressed or explicitly
      rationalised in the review file

## 3. Checks and external analysers

- [x] `gh pr checks 743` — list every check, flag failures
- [x] Failing check logs pulled and root-caused
- [x] qlty Cloud verdict (note staleness if local work is unpushed)
- [x] CodeQL alerts for the PR
- [x] Local `qlty smells` / `qlty check --no-fix` on changed files

## 4. Special-attention checks requested by the user

- [x] Dev container configuration changes — scrutinise very carefully and WARN
      the user prominently if any exist
- [x] No new `.md` files may be added by the PR — verify and flag
- [x] Never refer to the PR author in the third person as a distinct
      entity — that account is the user's own

## 5. Correctness / quality review of the diff

- [x] Data hard gate: no array holding two data types; no id list mixing id
      types; no discrimination by probing an optional field; no shape split in
      the domain but merged on the wire (or the reverse); invariants over a
      shared id space enforced across the union of split arrays
- [x] Coding standards: full names, type hints, no stray `Any`, small focused
      functions, no unrequested comments
- [x] HARD GATE: no `*.py` file over 250 lines (source and test)
- [x] Tests added/updated for new behaviour; isolated, no external state
- [x] 100% coverage on every added/modified/moved line
- [x] No tests removed, disabled, skipped or commented out
- [x] No lint/format/type config weakened (`ruff.toml`, `mypy.ini`,
      `pyproject.toml` lint sections, `.markdownlint.json`, etc.)
- [x] Correctness, regressions, security, coverage prioritised

## 6. Local verification

- [x] `task format` (no unstaged changes left)
- [x] `task lint`
- [x] `task type` (pyre — the CI gate)
- [x] `task type-pyright`
- [x] `task test`
- [x] `poetry run flake8 <changed modules> --max-line-length=120`
- [x] `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] Coverage run on changed modules
- [x] `task lint-md` if any markdown is touched
- [x] Runtime surface: run the modified backend service and exercise the
      affected route, or record why the change has no runtime surface

## 7. Produce the review document

- [x] `TASK-743-review.md` with metadata header (date, PR, branch, base,
      commit reviewed, reviewer, verdict)
- [x] Short friendly human-sounding summary section at the very beginning
- [x] `Details` subsection listing every finding with full details
- [x] Standard sections: `Summary`, `Findings`, `Severity`,
      `Reproduction Steps`, `Recommendation`
- [x] No line-length limit in the document (long lines allowed so it pastes
      cleanly into GitHub)
- [x] Every pre-existing PR finding explicitly addressed or rationalised
- [x] Do NOT commit or push anything
