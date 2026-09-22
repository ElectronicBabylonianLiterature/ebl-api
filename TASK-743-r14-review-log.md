# TASK-743-r14-review — Work Log

Round-14 review of PR #743. Records what was actually done, including errors and recoveries.

## Entries

### Start

- Read `.github/instructions/copilot.instructions.md` in full before any action.
- Identified the target: PR #743, `fix-type-checker-blind-spots` -> `master`, open, not a draft.
- Created this log and `TASK-743-r14-review-todo.md` before starting review work.

### Evidence gathering

- Confirmed no `.devcontainer/`, Docker, workflow, `pyproject.toml`, `Taskfile`
  or linter-config files appear in the PR diff. Dev container configuration is
  untouched — recorded as a verified negative for the user's standing warning.
- Pulled all PR feedback via `gh api`: 16 submitted reviews, 42 inline review
  comments, 2 issue comments. Reviewers: Fabdulla1 (human), sourcery-ai,
  qltysh, github-advanced-security (CodeQL).
- CI at HEAD `a0b74092`: CodeQL, Analyze (python), GitGuardian all green;
  `qlty check` reports "No blocking issues"; the three `Test Python` matrix
  jobs were still `in_progress` at review time.
- Code scanning alerts API returns HTTP 403 for this token, so CodeQL alert
  state was reconciled from the bot's PR comments plus the current tree.

### Local gates

- `task format` — 912 files already formatted, exit 0.
- `task lint` (ruff) — all checks passed.
- `task type-pyright` — 0 errors, 0 warnings on 161 changed files.
- `poetry run mypy <161 changed files> --ignore-missing-imports` — success,
  no issues.
- `poetry run flake8 <161 changed files> --max-line-length=120` — 0 errors.
- `task lint-md` — 3 MD013 errors, all in this round's own task files.
  Recovered by adding the repo's established
  `<!-- markdownlint-disable MD013 -->` header, matching the existing
  `TASK-*.md` convention. No linter configuration was touched.

### Errors made and recovered

- First attempt at the background test run used a trailing `&` inside an
  already-backgrounded Bash call; the wrapper shell exited immediately and
  produced an empty log. Recovered by re-running without `&`.
- First `task type` (pyre) run aborted with
  `Worker.Worker_exited_abnormally` while the full test suite was running
  concurrently — a resource failure, not a type error. Re-run scheduled once
  the machine is quiet; the result is not inferred from pyright or mypy.
- Discovered that `MONGODB_URI` in this dev container's environment points at
  the production replica set. All local commands are therefore run under
  `env -u MONGODB_URI` so no gate can reach the live cluster.

### Verification against the running service

- Started the real WSGI app (`ebl.app.create_app` under waitress) twice: HEAD
  `a0b74092` on port 8099 and a detached `origin/master` worktree on 8098,
  both against a scratch MongoDB at `127.0.0.1:27017/ebl_r14_review`.
- Route evidence (HEAD vs master), same seeded data:
  - `GET /signs?listAll=true` — master **500**, HEAD **200** `["KU","NA"]`.
  - `GET /signs/transliteration/[[[` — master **500**, HEAD **422**.
  - `GET /signs/transliteration/ku-` — master **500**, HEAD **422**.
  - `GET /markup?text=@i{unclosed` — master **500**, HEAD **422**.
  - `GET /signs/transliteration/ku` — **200** on both, identical body.
  - `GET /signs?value=ku&subIndex=abc` — **422** on both.
  - `GET /signs?listAll=true&value=ku` — **422** on both.
- Legacy-shape migration path: inserted one fragment whose stored
  `nameParts` are the old interleaved arrays with no `nameBreaks` key, then
  read `GET /fragments/X.0` from both services. HEAD returned 24 named signs,
  0 of them mixing token types in `nameParts`, all 24 carrying `nameBreaks`
  (3 non-empty). Master returned the same 24 signs with 3 mixed `nameParts`
  arrays and no `nameBreaks`. Every `name`, `value` and `cleanValue` matched
  between the two, so the separation is lossless.
- First attempt at that check returned 500 from both services. Cause was my
  own seed: the factory fragment carried `archaeology.site = "Assyria"` and I
  had not seeded the provenance collection. Not a PR defect; recovered by
  dropping `archaeology` from the seeded document.

### Remaining gates

- `task type` (pyre) re-run on a quiet machine — **No type errors found**.
- Full suite — 4773 passed, 2 skipped, 1 xfailed, 0 failures (609.89s).
- `qlty smells --all --include-tests` at HEAD and at `origin/master` in the
  detached worktree, diffed: 107 findings at HEAD against 132 at master.
  The branch removes 28 and introduces 3, all `similar-code` between `__all__`
  export lists. `TASK-743-r13-qlty-log.md` already records the investigation
  and the decision to justify them, which the instructions' own carve-out
  allows.

### Coverage

- Full suite under `--cov=ebl`: 4773 passed, repo-wide 97% (18 231 statements,
  611 missed). Cross-referenced `coverage.json` against the 68 changed source
  files: **every one is at 100%**, none below, none unmeasured.
- The 93 changed test files are not measured because `.coveragerc` sets
  `omit = ebl/tests/*` — the project's own configuration.

### Output

- Wrote `TASK-743-r14-review.md`: metadata header (PR, branch, head SHA, date,
  verdict, blocking items, CI state, dev container verdict), a short
  human-readable `Review` section with a `Details` subsection carrying every
  finding in full, then the required `Summary` / `Findings` / `Severity` /
  `Reproduction Steps` / `Recommendation` sections.
- `<!-- markdownlint-disable MD013 -->` at the top removes the 80-column limit
  for this document so it pastes cleanly into GitHub, matching the convention
  the existing `TASK-*.md` files already use. No linter configuration file was
  modified.
- First `task lint-md` on the finished review reported 7 MD036 errors
  (bold-as-heading in Reproduction Steps). Recovered by promoting those labels
  to `###` headings; lint-md is now 0 errors across all 40 files.
- Verdict: code approved, merge blocked on three release gates — R14-1 (34
  stray files, closable here), R14-2 (frontend `nameBreaks`), R14-3 (#764
  migration dry run).
- Nothing was committed or pushed. The working tree holds only the three new
  untracked round-14 task documents.

<!-- markdownlint-configure-file { "MD013": false } -->
