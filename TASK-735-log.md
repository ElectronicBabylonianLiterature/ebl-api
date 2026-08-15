# TASK-735 Work Log — Review PR #735

Task: Review PR #735, fetching all reviews and comments (Sourcery AI, other
bots, human reviewers), failing checks, and qlty issues.

## Entries

### 1. Task start

- Read `.github/instructions/copilot.instructions.md` in full before acting.
- User rejected an initial `gh pr view` call bundled with a branch check,
  stating they had just checked out the correct branch. Recovered by
  re-running only the branch/log inspection first, then PR metadata.
  Lesson applied: do not bundle assumptions about branch state into the
  first command.
- Confirmed branch `add-realia-slugs-endpoint`, PR #735, base `master`,
  state OPEN, 11 files changed (+388/-4), `mergeable: CONFLICTING`.

### 2. Task artifacts created

- Created `TASK-735-todo.md` and `TASK-735-log.md` before starting review
  work, per the task-tracking hard gate.

### 3. PR feedback fetched (review hard gate)

- `gh api .../pulls/735/reviews` — 5 reviews: 1 Sourcery (COMMENTED),
  4 from Fabdulla1 (2 CHANGES_REQUESTED, 2 empty COMMENTED wrappers).
- `gh api .../pulls/735/comments` — 4 inline comments (2 Sourcery, both
  self-marked addressed; 2 Fabdulla1 from 2026-07-29, both open).
- `gh api .../issues/735/comments` — 1 Sourcery reviewer's guide.
- `git log --merges origin/master..HEAD` — no merge commits, so no
  merged-in PR whose feedback also needs fetching.

### 4. Checks and qlty

- All 13 check runs pass (2 docker skipped). CodeQL, GitGuardian,
  Sourcery, Analyze, Test 3.11/3.12/pypy-3.11 all green.
- Commit statuses: `qlty check`, `qlty coverage`, `qlty coverage diff`
  all `success`. Combined status `success`.
- The qlty issues detail page requires sign-in (302 → /login), so the
  green status is the available evidence; no qlty annotations or
  comments exist on the PR.
- Local `qlty check` not possible: repo has no tracked `qlty.toml`
  (`qlty` CLI reports "Qlty must be set up in this repository").

### 5. Empirical verification (running-service hard gate)

- Could not use `task start`: `Taskfile.dist.yml` has `dotenv: [".env"]`
  and `.env` `MONGODB_URI` points at the production cluster. Built a
  scratch runner instead that pins `MONGODB_URI=mongodb://127.0.0.1:27017`
  and a throwaway database, generates a local RSA key for `AUTH0_PEM`,
  and serves `ebl.app.create_app(create_context())` via waitress on
  127.0.0.1:8123.
- Exercised the live route: `/realia/ids` → 200, correctly sorted
  (case/accent-insensitive), redirect stub excluded,
  `Cache-Control: public, max-age=600`.
- `/realia/all` → 200 and returns the entry whose `_id` is `all`,
  confirming the earlier `/realia/all` collision was fixed by the rename.
- `/realia/ids` shadows an entry whose `_id` is `ids`: the ID appears in
  the list body but the entry itself is unreachable; `/realia/by-id/ids`
  → 404 because `realiaId` is blank. Fabdulla1's open comment confirmed.
- Malformed-legacy-document reproduction: first attempt was inconclusive
  because `$and`/`$or` short-circuit and never evaluated `$size` on the
  scalar field. Recovered by reshaping the fixture so the document is
  redirect-shaped (`crossReferences` with exactly 1 entry), which forces
  evaluation. Result: `OperationFailure: The argument to $size must be an
  array` and `input to $filter must be an array`. Against the running
  service, one such document makes `/realia/ids` return **HTTP 500**
  while `/realia/Anu` still returns 200. Fabdulla1's second open comment
  confirmed.

### 6. Local gates run as review evidence

- `task format` → exit 0, 733 files already formatted.
- `task lint` (ruff) → exit 0, all checks passed.
- `task type` (pyre) → exit 0, "No type errors found".
- `task type-pyright` → 0 errors, 0 warnings, 0 informations.
- `poetry run mypy <8 changed modules> --ignore-missing-imports` → 0
  errors in the changed files (the 50 reported errors are all in
  untouched transitively-imported modules, pre-existing on master).
- `poetry run flake8 <8 changed modules> --max-line-length=120` → exit 0.
- `poetry run pytest ebl/tests/realia --cov=ebl/realia` → 91 passed,
  **100% coverage** on every realia module, 0 missing lines.
- All changed `.py` files are within the 250-line limit (largest:
  `mongo_realia_repository.py` 157, `test_realia_list_ids.py` 151).
- Full suite started in the background for regression evidence.

### 7. Mistake made and corrected

- I initially assumed the `copilot.instructions.md` I read at session
  start was this branch's version. It was not: the user had checked out
  a different branch at that point. The branch's copy is an older,
  7-gate variant; `origin/master` carries the authoritative 8-gate
  version. I have been following the master version throughout, which
  is the stricter one. This discrepancy is itself a review finding.

### 8. Review written and gates re-confirmed

- Wrote `TASK-735-review.md` using the required template sections:
  Summary, Findings, Severity, Reproduction Steps, Recommendation.
- First draft failed `task lint-md` with 28 errors (MD060 table pipe
  spacing and MD013 line length, from wide markdown tables). Recovered
  by rewriting every table as a list and rewrapping to 80 columns;
  `task lint-md` then reported 0 errors across 7 files.
- Full suite finished: **3808 passed, 2 skipped, 1 xfailed**, exit 0,
  in 249s. No regressions.
- Findings recorded: 2 High open reviewer issues reproduced live
  (route shadowing of `_id == "ids"`; 500 from a malformed legacy
  document), 1 High merge-conflict/scope issue, 1 Medium stale PR
  title and body, 1 Medium domain question on the exactly-one
  cross-reference rule, 3 Low.

### 9. Cleanup

- Stopped the local waitress service and dropped the scratch database
  `ebl_review_735`.
- Working tree contains only the three TASK-735 markdown files; no
  source file was modified during this review.
- **Nothing committed or pushed.** No commit was requested.
