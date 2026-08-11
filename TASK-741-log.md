# TASK-741 Work Log — Review PR #741

## 2026-08-11

- Read `.github/instructions/copilot.instructions.md`; applying all hard gates.
- Identified PR #741 "Fix AfO Register texts-numbers match for references
  containing spaces" on branch `fix-afo-register-texts-numbers-split`.
- Noted `mergeable: CONFLICTING` from `gh pr view` — merge conflict vs `master`.
- Branch diff vs master: 6 files, +254/-64.
- Created `TASK-741-todo.md` and this log.

### Feedback collection (Review Guidelines hard gate)

- `gh api .../pulls/741/reviews` — 2 reviews: sourcery-ai[bot] `COMMENTED`
  (`4734372789`, remove task scaffolding), Fabdulla1 `CHANGES_REQUESTED`
  (`4753124320`, 3 points: bound the endpoint, ambiguous-reference test,
  candidate dedup).
- `gh api .../pulls/741/comments` — empty, no inline diff comments.
- `gh api .../issues/741/comments` — 1 comment: sourcery-ai Reviewer's Guide
  (`5021576863`), informational.
- GraphQL `reviewThreads` — `totalCount: 0`; `reviewDecision:
  CHANGES_REQUESTED`; `mergeStateStatus: DIRTY`.
- Merged-in branches: `git log --merges` shows only `7a2d3285`, a merge of
  `origin/master`. No feature-branch PRs merged in, so no extra PR feedback.

### CI / qlty

- All checks on head `8e30b353` pass (3.11 / 3.12 / pypy-3.11 on both workflow
  runs, Analyze (python), CodeQL, GitGuardian x2, GitGuardian Security Checks).
- `qlty check` success "No blocking issues"; `qlty coverage` 95.5% (+0.1%);
  `qlty coverage diff` 100.0% vs 75% threshold.
- `Sourcery review` **skipped** — "Auto re-review limit reached"; the last two
  commits have no Sourcery coverage.
- Local `qlty check` unavailable — repo not `qlty init`-ed in this workspace;
  relied on the CI check plus local coverage/flake8/mypy runs.

### Local verification

- `poetry run pytest ebl/tests/afo_register
  ebl/tests/fragmentarium/test_retrieve_annotations.py --cov=ebl/afo_register
  --cov-report=term-missing` — 41 passed, 100% coverage on all
  `ebl/afo_register` modules.
- `poetry run flake8 <changed> --max-line-length=120` — clean.
- `poetry run mypy <changed> --ignore-missing-imports` — 0 errors in changed
  files (87 pre-existing errors elsewhere, unrelated modules).
- 250-line cap: 151 / 73 / 216 / 159 / 126 lines — all pass.
- Confirmed the test suite uses `pymongo_inmemory` outside CI and refuses
  production database names, so the production `MONGODB_URI` present in the
  shell environment was never used.

### Reproduction work

- Wrote a temporary repro test under `ebl/tests/afo_register/` driving the real
  falcon app via the `client` fixture. First attempt returned 422 because
  `str.replace` lengthened the queries past `MAX_QUERY_LENGTH`; corrected to
  build exactly-500-character distinct queries.
- Confirmed: a 504 KB valid body → **HTTP 500**. Measured
  `_build_candidate_query` output: 166,000 `$or` clauses, 1.59 s build time,
  141.8 MB peak allocation, 85.4 MB BSON — over MongoDB's 16 MB limit.
- Deleted the temporary test file after measuring; the repro is recorded in
  `TASK-741-review.md` instead.

### Output

- Wrote `TASK-741-review.md` (Summary / Findings / Severity / Reproduction
  Steps / Recommendation) with 10 findings; verdict: request changes.
- `task lint-md` — 0 errors.
- No production code was modified during the review itself.

## 2026-08-11 — addressing the findings

- Restored `.gitignore` and `ebl/tests/fragmentarium/test_retrieve_annotations.
  py` from `origin/master`; `git diff origin/master --stat` on both paths is
  now empty, so the merge conflict source is gone.
- `afo_register_records.py`: extracted `validate_query`, added
  `MAX_QUERY_TOKENS = 24`, and replaced `str(req.media)` in the 404 message
  with the query count.
- `mongo_afo_register_repository.py`: restored the `isinstance(query, str)`
  guard in `candidate_splits`; added `MAX_CANDIDATES` with a `DataError` raise
  in `_build_candidate_query`. Confirmed `DataError` is not a `ValueError`
  subclass, so `on_post`'s `except ValueError` does not swallow it, and
  `ebl/error_handler.py:39` maps it to 422.
- Sized `MAX_CANDIDATES`: 5000 first, but that rejected a 1000-item batch of
  6-token references, so raised to 10000. Measured worst case at that cap:
  9,982 clauses, 0.083 s, 8.2 MB peak, 4.78 MB BSON.
- Extracted `ebl/tests/afo_register/test_afo_register_candidate_query.py` and
  moved `test_build_candidate_query_deduplicates_candidates` there verbatim
  (moved, not removed) to stay under the 250-line cap.
- Added tests: non-string guard, split enumeration, no-candidate case,
  at-limit and over-limit candidate counts through both the private method and
  `search_by_texts_and_numbers`, plus three route-level 422 cases.
- Re-ran the temporary repro: the original 504 KB body now returns 422, the
  post-cap worst case returns 422, and a realistic 1000-reference batch still
  returns 200. Temporary repro file deleted afterwards.
- Gates: 51 tests passed with 100% coverage on `ebl/afo_register`;
  `task format` clean; `task lint` (ruff) clean; flake8 clean; mypy clean on
  changed files; `poetry run pyre check` reports no `afo_register` errors;
  `task lint-md` 0 errors; line counts 160 / 80 / 205 / 188 / 72.
- Correction: `task type-pyright` is missing from **this branch's**
  `Taskfile.dist.yml` but exists on `origin/master` — the branch predates it.
  Ran pyright directly with master's command
  (`npx pyright@1.1.411 <changed .py files>`). It reported one error the other
  checkers missed: passing `None` to `candidate_splits(query: str)` in the new
  guard test. Widened the parameter to `object` so the `isinstance` guard is
  verifiable; pyright, pyre, mypy, ruff and flake8 are all clean afterwards.
- `task test` (full suite): **3868 passed, 2 skipped, 1 xfailed** in 300.76 s,
  exit code 0. The skips and the xfail are pre-existing and unrelated.
- Re-ran `task test` after the `candidate_splits` annotation widening:
  **3868 passed, 2 skipped, 1 xfailed** in 275.53 s, exit code 0.

## 2026-08-11 — commit and merge (explicitly requested by the user)

- Re-ran the pre-commit gates on the exact tree before committing: `task
  format` clean, `task test` 3868 passed, 100% coverage on changed modules,
  flake8 0 errors, mypy 0 errors in changed files.
- Committed `5b716e5b` "Bound texts-numbers query expansion and restore
  candidate type guard" with the 7 code files only. The `TASK-741-*.md` and
  files were deliberately left untracked at that point — they are scaffolding
  to be deleted before merge.
  ggshield secret scan passed.
- `git merge origin/master --no-edit` → merge commit `7fc44160`, **no
  conflicts** (7 incoming commits: #727, #740, #744, #745, #747, #748, #749).
  `git diff origin/master --stat` now lists only the five `afo_register` files;
  `.gitignore` and `test_retrieve_annotations.py` no longer differ from master.
- `task type-pyright` is available again after the merge.

### Gates on the merged tree

- `task test` — **4319 passed, 2 skipped, 1 xfailed** in 350.10 s, exit 0.
- Coverage — 100% on every `ebl/afo_register` module (44 tests).
- `task format` — 802 files already formatted.
- `task lint` (ruff) — all checks passed.
- `poetry run flake8 ... --max-line-length=120` — 0 errors.
- `task type-pyright` — 0 errors.
- `poetry run mypy ... --ignore-missing-imports` — 0 errors in changed files.
- `task type` (pyre) — "No type errors found", exit 0. The first attempt
  crashed with `internal exception: End_of_file` because it was run
  concurrently with the full test suite; re-running it alone was clean.
- `task lint-md` — 0 errors.

### Unrequested push — 14:57:01

The branch reached GitHub without `git push` ever being run in this session.

- `git reflog show origin/fix-afo-register-texts-numbers-split` records
  `7fc44160 ... update by push` at **2026-08-11 14:57:01 +0000**, roughly five
  minutes after the merge commit was created at 14:51:53. During that window
  only read-only gates were running (`task format`, `task lint`, flake8,
  `task type-pyright`).
- `git ls-remote origin` confirms the remote branch is at `7fc44160`.
- `.git/hooks` contains only `pre-commit` (pre-commit.com) and `pre-push`
  (blocks direct pushes to `master`); neither pushes anything. No push-related
  git config is set.
- `.vscode/settings.json` sets no `git.postCommitCommand`; the only matches
  for that setting name on disk are extension caches and logs. The mechanism
  was not identified. A manual sync from the IDE, which is open on this repo,
  fits the timing just as well as an automatic one.

PR #741 consequently now reports `mergeable: MERGEABLE` (was `CONFLICTING`),
head `7fc44160`, `mergeStateStatus: BLOCKED` on the standing
`CHANGES_REQUESTED` review. CI on that head finished at 13 pass / 3 skipping
(Sourcery review and the two `docker` jobs), nothing failing.

## 2026-08-11 — task docs committed, then removed

At the user's request these task-tracking files are committed once for the
record and then deleted in a follow-up commit, matching how the earlier
`TASK-afo-register-link-*.md` pair was handled on this branch and satisfying
Sourcery review `4734372789`.

Correction: earlier entries in this log and in `TASK-741-review.md` referred to
`TASK-743-docs-cleanup-todo.md` and `TASK-743-docs-cleanup-log.md`. Those files
do not exist and never did. The three untracked files present at the start of
the session were `TASK-741-log.md`, `TASK-741-review.md` and
`TASK-741-todo.md`, left over from an earlier session and overwritten here. A
`find` for `TASK-*.md` confirms these three are the only task docs in the
repository, and none of them were tracked. Those references have been fixed.

No Python file changed between the merge verification above and these two
commits, so the `task test` / coverage / flake8 / mypy / pyre / pyright results
recorded for `7fc44160` still describe the committed tree.
