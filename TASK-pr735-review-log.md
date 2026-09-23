# TASK pr735-review — Log

## 2026-09-23

- Read `.github/instructions/copilot.instructions.md` in full.
- Session git snapshot claimed branch `fix-type-checker-blind-spots`; actual
  checkout is `add-realia-slugs-endpoint` (HEAD `ad222eb3`, in sync with
  origin). The `fix-type-checker-blind-spots` PR (#743) is already merged, so
  the PR under review is #735 for the checked-out branch.
- Created this log and the TODO before starting review work.
- Fetched PR #735 metadata: open, `mergeable=MERGEABLE`,
  `mergeStateStatus=BLOCKED`, `reviewDecision=CHANGES_REQUESTED`, 12 files,
  +536/−7, 16 commits, head `ad222eb3`. Merge base `2169b155`, master is at
  `cd46110c` (ahead).
- Fetched feedback: 6 reviews (1 Sourcery, 5 Fabdulla1, the latest one
  CHANGES_REQUESTED on `ad222eb3`), 4 inline comments (2 Sourcery resolved, 2
  Fabdulla1 **unresolved**), 1 issue comment (Sourcery reviewer's guide, stale —
  describes the first iteration).
- The only merge in the branch is `origin/master` (0f37a27f); no feature PR
  branch is merged into this one, so no other PR feedback needs fetching.
- CI checks on `ad222eb3`: all pass (tests 3.11/3.12/pypy, CodeQL "No new
  alerts", GitGuardian, qlty check "No blocking issues", qlty coverage diff
  100%). `docker` and `Sourcery review` skipped.
- CodeQL alerts REST API returns 403 for this token; used the CodeQL check-run
  output instead ("No new alerts in code changed by this pull request").
- qlty web issue page redirects to login (302). Ran local `qlty check` + `qlty
  smells` on changed files instead: 40× bandit B101 (assert in tests, the same
  on untouched test files, e.g. `test_realia_route.py` has 32), 7× qlty-mypy
  `call-arg` (to cross-check against the real mypy gate). Smells: no findings.
- Read the full source diff (8 source files) and the 4 test files. Read
  `RealiaEntrySchema`, `ebl/cache/application/cache.py` and the existing
  `cache.cached(...)` users.
- Compared the stub rule with ebl-frontend `origin/master` (`e281f7ba`)
  `hasOwnContent`/`getRedirectTarget` in `src/realia/domain/RealiaEntry.ts`: the
  backend rule matches (afoRegister/references/afoCrossReferences non-empty,
  `reallexikon.length > 1`, any resolvable reallexikon reference; redirect iff
  no own content and exactly one cross-reference). Frontend calls `/realia/all`
  (`RealiaRepository.ts:160`).
- Checked that `master` has not touched `ebl/realia` or `ebl/cache` since the
  merge base (no drift).
- Checked the Realia write paths: the API has none (the collection is imported
  externally), so the `all` reservation can only be enforced at listing time.
- Gates (all on HEAD `ad222eb3`, clean tree):
  - `task format` exit 0; `task lint` exit 0; `task type` (pyre) "No type errors
    found"; `task type-pyright` 0 errors on the 12 changed files.
  - `poetry run mypy <changed> --ignore-missing-imports`: 0 errors in the
    changed files; 26 errors in 17 transitively imported, unchanged files
    (pre-existing, not in the PR's diff).
  - `poetry run flake8 <changed> --max-line-length=120`: exit 0.
  - Coverage of the changed source modules: 100% (357 statements). Repo
    `.coveragerc` omits `ebl/tests/*`; measured those with a scratch config: new
    test files 100%, `test_realia_info.py:37` (the PR's added fake `raise
    NotImplementedError()`) uncovered.
  - Full suite `poetry run pytest -n auto`: 4416 passed, 2 skipped, 1 xfailed,
    exit 0.
  - Max changed `.py` length 181 lines (≤ 250). No new `.md` files in the PR. No
    dev container / Docker / CI / tooling config changes in the PR.
- Runtime: served the real app (`get_app` via waitress, port 8735) against local
  mongod `127.0.0.1:27017`, throwaway DB `ebl_review_pr735`, never `.env`.
  - `GET /realia/all` → 200, `Cache-Control: public, max-age=600`, sorted
    accent/case-insensitively, `Pig` (stub) and `all` (reserved) excluded,
    `TwoCross` listed and `/realia/TwoCross` → 200, `a/b` → 200 through the
    sink.
  - Listed but `/realia/{id}` → 500: `NullType` (`type: null`, `ValidationError:
    Field may not be null`), `NullRealiaId` (`realiaId: null`), `BadElement`
    (`relatedTerms: [5]`).
  - Inserted `{"_id": 42}` → the whole `/realia/all` returns 500 (`TypeError:
    normalize() argument 2 must be str, not int`).
  - Mongo profiler: 3 × `GET /realia/all` → 3 `realia` queries (no server-side
    caching).
- Errors I made and recovered:
  - The session snapshot named the wrong branch; resolved via `git status` / `gh
    pr list` before starting.
  - The first `qlty` grep used a regex ugrep rejected; reran with a simpler
    filter.
  - The first server start failed with `ModuleNotFoundError: ebl` (script in the
    scratchpad, repo not on `sys.path`); restarted with
    `PYTHONPATH=/workspaces/ebl-api`.
  - Deleted the generated `.coverage` file (gitignored; produced by my own
    coverage runs).
- Stopped the server (pid 81927) and dropped `ebl_review_pr735`.
- Wrote `TASK-pr735-review.md`: metadata table, "Quick take", Summary
  (feedback and checks tables), Findings table with a Details subsection
  (D1–D7), Severity, Reproduction Steps, Recommendation. It is not
  hard-wrapped (as requested), with `<!-- markdownlint-disable MD013 -->` at
  the top so `task lint-md` still passes. No GitHub username of the PR owner
  appears in it.
- Marked one D2 sub-claim (cross-reference missing `lemma`) as derived from
  the schema, not reproduced at runtime.
- Error: my TODO/log were written with long lines and failed `task lint-md`
  (29 × MD013). Rewrapped both to 80 columns; `task lint-md` → 0 errors.
- Re-read `.github/instructions/copilot.instructions.md`; every section
  checked. Nothing committed or pushed; no code changed.
