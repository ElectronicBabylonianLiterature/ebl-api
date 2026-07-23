# TASK-740 Review — Work Log

## Task

Review PR #740 "Realia annotation API: resolve realiaInfo on every
fragment-returning route". Fetch all reviews and comments including qlty.
Investigate failing tests.

## Log

### Step 1 — Tracking files

Created `TASK-740-review-todo.md` and `TASK-740-review-log.md` before starting
any investigation, per the task-tracking hard gate.

Note: the branch previously had TASK-740 tracking docs which were removed in
commit `0c7ec147`. Per the instructions, removal settles that PR only; this new
task starts by creating them again.

### Step 2 — Gathering PR state

PR #740, `add-realia-annotation-api` -> `master`, open, not draft.
Head at review time: `d99cd834`.

Feedback fetched via `gh api`:

- `/pulls/740/reviews` — 3 reviews: sourcery-ai (skipped, diff too large),
  Fabdulla1 (CHANGES_REQUESTED, 2 substantive concerns), qltysh (COMMENTED).
- `/pulls/740/comments` — 12 inline comments, all from qltysh: 10
  `function-parameters` and 2 `similar-code`.
- `/issues/740/comments` — none.
- No PRs merged into this branch other than `origin/master` (`0b62f9fc`).

### Step 3 — Failing tests

`gh pr checks 740`: `Test Python 3.12` failed on both workflow runs
(29934731178 and 29934734561); the 3.11 / pypy jobs were cancelled by
fail-fast in one run and passed in the other. Everything else passes; qlty
check reports 12 blocking issues.

Both failures are the same single test:

    FAILED ebl/tests/fragmentarium/test_fragment_repository_query.py
      ::test_query_fragmentarium_number

Failure shape: querying `{"number": "X.251"}` returned more than the one
expected fragment.

Root cause found and reproduced locally:

- `number_is()` (`ebl/fragmentarium/infrastructure/queries.py:46`) builds an
  `$or` over `externalNumbers.cdliNumber`, `museumNumber`, `accession` and
  `archaeology.excavationNumber`.
- `FragmentFactory.number` mints `MuseumNumber("X", str(n))`
  (`ebl/tests/factories/fragment.py:245`) and
  `ArchaeologyFactory.excavation_number` mints `ExcavationNumber("X", str(n))`
  (`ebl/tests/factories/archaeology.py:71`) — same prefix, **independent**
  sequence counters.
- When the two counters cross, one fragment's museum number equals another
  fragment's excavation number, the `$or` legitimately matches both documents,
  and the test's single-item expectation fails.

Reproduced deterministically with a scratch test that forces the collision
(`ExcavationNumber` of fragment B set to fragment A's museum number):
`QUERIED: X.0 / RETURNED: ['X.0', 'X.1']`. Scratch file was written outside
the repo and removed after the run.

The test file, the factories and `number_is` are all untouched by this PR.
The PR does add and split many `ebl/tests/fragmentarium/*` files, which shifts
how many factory instances each xdist worker builds and therefore where the
counters land — surfacing a latent test-isolation defect. Master's own test
jobs are green (run 29823535384); the recent master run failures are
Dependabot jobs, not tests.

### Step 4 — Local gates

| Gate | Result |
| --- | --- |
| `task format` | 775 files already formatted; no unstaged changes |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `task test` (`pytest -n auto`) | 3933 passed, 2 skipped, 1 xfailed |
| `task lint-md` | 0 errors |
| `flake8 --max-line-length=120` | 1 × E203 at `fragment.py:202` |
| `mypy --ignore-missing-imports` | 10 errors in changed files |
| 250-line file limit | all within limit; longest is 240 |

Notes on the two non-clean gates:

- E203 is in the repo's own ruff ignore list (`pyproject.toml:69`), is a
  known black/ruff-format vs PEP 8 conflict, and the line
  (`self.text.text_lines[numbers[0] : numbers[1] + 1]`) is **not** touched by
  this PR.
- All 10 mypy errors were verified pre-existing by running mypy against an
  `origin/master` worktree: the same errors appear at shifted line numbers.
  The branch in fact *removes* two of them (`fragment.py` generator item type,
  `text_line.py` invalid index type). No new mypy error is introduced. They
  still fail gate 8 as written ("a pre-existing error in a file you touched is
  not acceptable"), so they are reported as a finding.

The full local suite is green while CI fails, which is consistent with the
xdist-distribution-dependent factory-counter collision diagnosed in step 3.

### Step 5 — Live service verification

Ran the real Falcon app (`ebl.app.create_app`) on a `wsgiref` HTTP server
against a real mongod, and issued real HTTP requests. Results:

    GET  /fragments/X.0                  200  realiaInfo: []
    GET  /fragments/X.0/named-entities   200  namedEntities [], realia []
    POST /fragments/X.0/named-entities   200  realiaInfo: [realia_1]
    GET  /fragments/X.0                  200  realiaInfo: [realia_1]
    GET  /fragments/X.0/named-entities   200  realia: [Realia-1 -> Word-1]
    GET  /fragments/retrieve-all?skip=0  200  realiaInfo: []
    POST unknown realiaId                422  Unknown realiaId: realia_999
    POST duplicate id across arrays      422  Conflicting annotation ids
    POST realiaId inside namedEntities   422  unknown-field error
    POST namedEntities not a list        422  Invalid 'namedEntities'
    POST malformed realiaId "nope"       422  pattern mismatch
    POST type "PersonalName"             500  DEFECT

The last case is a real defect found only by running the service — see
finding 2 in `TASK-740-review.md`. My first live run used the invalid type
string `"PersonalName"` in the duplicate-id payload and so mis-attributed the
500 to the uniqueness check; re-running with the valid `"PERSONAL_NAME"`
isolated it to the type field. Recording the mistake as required.

Scratch service-check modules were written to the scratchpad, copied into
`ebl/tests/fragmentarium/` only for the duration of each run, and deleted
afterwards. Working tree contains no leftovers.

### Step 6 — Coverage

Ran the full suite with
`--cov=ebl.fragmentarium --cov=ebl.transliteration --cov=ebl.realia
--cov-report=term-missing`. Result: 3933 passed, TOTAL 97%.

Of the 36 changed source modules, 35 report 100%. The one exception is
`ebl/fragmentarium/infrastructure/mongo_fragment_repository.py` at 98%,
missing line 117 — the `raise ValueError("Unexpected update field ...")`
guard. Checked with `git diff -U0`: the PR's only hunk in that file is
`@@ -113 +113 @@`, a single-line in-place replacement, so line 117 is
neither added, modified nor moved. Touched-lines coverage is therefore
100%. Recorded in the review as a note, not as a finding against the PR.

### Step 7 — Review file

Wrote `TASK-740-review.md` using the required template sections
(`Summary`, `Findings`, `Severity`, `Reproduction Steps`,
`Recommendation`), plus sections recording every existing PR feedback
item and every gate run.

First draft failed `task lint-md` with 32 errors (MD013 line length,
MD046 fenced-versus-indented code blocks, MD036 emphasis-as-heading).
Rewrote all three markdown files with indented code blocks, headings
instead of bold labels, and lines within 80 columns rather than touching
the lint configuration, which is forbidden. `task lint-md` now reports
0 errors.

### Step 8 — Cleanup and state

Working tree contains only the three untracked review files
(`TASK-740-review.md`, `TASK-740-review-todo.md`,
`TASK-740-review-log.md`). The temporary `origin/master` worktree used
for the mypy baseline was removed (`git worktree list` shows only the
main tree). No scratch test modules remain under `ebl/`. Nothing was
committed or pushed.
