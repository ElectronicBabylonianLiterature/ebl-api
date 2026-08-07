# TASK-743-review — Work Log

Detailed log of the review of PR #743. Records what was actually done,
including every error made and how it was recovered.

## Entries

### 1. Read instructions, established task identity

- Read `.github/instructions/copilot.instructions.md` in full before acting.
- Ran `gh pr view` to identify the PR under review: **#743**, "Make the ATF
  parser visible to the type checkers", `fix-type-checker-blind-spots` ->
  `master`, state OPEN, mergeable MERGEABLE, not a draft.
- Created `TASK-743-review-todo.md` and this log before starting review work,
  per the task-tracking hard gate. Existing `TASK-743-fixes-*`,
  `TASK-743-merge-*` and `TASK-743-size-*` files belong to earlier tasks and
  are not carried forward as this task's artefacts.

### 2. Feedback gathering

- `gh api .../pulls/743/reviews` — 2 submitted reviews: `sourcery-ai[bot]`
  (COMMENTED, 1 issue) and `qltysh[bot]` (COMMENTED, empty body). No human
  reviews on this PR.
- `gh api .../pulls/743/comments` — 6 inline comments: 1 from Sourcery,
  5 from qlty.
- `gh api .../issues/743/comments` — 1 Sourcery "Reviewer's Guide" summary.
- Branches merged into this one: only `master` (525c4979). No unmerged
  feature branch was merged in, so there is no sibling PR whose feedback
  needs pulling. Related PR #740 (this PR was *split out of* it) is MERGED;
  its feedback was fetched anyway and is qlty parameter-count/duplication
  noise on files not in this diff.

### 3. CI checks

`gh pr checks 743` at head 19a2f464:

- CodeQL: pass. Analyze (python): pass. GitGuardian x2: pass.
- Sourcery review: skipping.
- qlty check: pass, but reports **5 blocking issues**.
- Test Python 3.11 / 3.12 / pypy-3.11 (two workflow runs): **in_progress**
  at the time of review.

CI (`.github/workflows/main.yml`) runs only `ruff check`, `ruff format
--check` and `pyre check`. It does **not** run pyright, mypy or flake8.

### 4. Local gates

- `poetry run task test-all` -> **failed at `type-pyright`, exit 123**.
  - `format` (ruff format --check): pass.
  - `lint` (ruff check): pass.
  - `type` (**pyre**): "No type errors found" — pyre passes here, contrary
    to the PR body which claims it could not be run. Recorded as a
    correction to the PR description.
  - `type-pyright`: **149 errors, 1 warning**. Suite aborted here, so
    `test` and `lint-md` did not run under `test-all`.
- Ran `pytest` separately (see below).
- `mypy --ignore-missing-imports` on the 59 changed files: 5 errors, all in
  files **not** touched by this PR (`legacy_atf_transformers.py`,
  `logger.py`, `lemmatization.py`, `atf_indexing_visitor.py`), reached only
  transitively. Gate 8 as scoped ("changed files") passes.
- `flake8 --max-line-length=120` on changed files: **0 errors**.
- 250-line gate: largest changed `.py` is 249 lines
  (`lemmatized_fragment_text.py`, `legacy_atf_converter.py`). Passes.

### 5. Pyright baseline (to separate regression from pre-existing debt)

Created a detached worktree at `origin/master`, symlinked the project
`.venv` into it (no `pyrightconfig.json`/`[tool.pyright]` exists, so pyright
relies on `.venv` discovery), and ran the same pyright version on master's
copies of the 40 changed files that exist there.

- master baseline: **173 errors**
- this branch: **149 errors**

Per-file comparison shows no file regressed. The PR clears pyright in its
target files (`lark_parser.py` 5->0, `legacy_atf_converter.py` 7->0,
`legacy_atf_line_validator.py` 3->0, `sign_tokens.py` 3->0,
`chapter_schemas.py` 4->0, `corpus_search_aggregations.py` 2->0,
`test_app_bootstrap.py` 1->0). The remaining counts are relocations:
`fragment.py` 106 -> `fragment.py` 19 + `fragment_metadata_factories.py` 87
(= 106 exactly). So the 149 is pre-existing debt in touched files, not a
regression — but gate 4 demands zero, so the gate still fails.

**Error made and corrected:** my first read of the 149 errors was that the
branch had introduced them. Building the master baseline before writing the
finding showed the opposite (173 -> 149, a net improvement). The finding was
rewritten from "introduces 149 pyright errors" to "leaves 149 pre-existing
pyright errors in files it touched, failing gate 4".

### 6. qlty findings triaged against master

All 5 blocking qlty issues are pre-existing code relocated by the file
splits, verified against `git show origin/master:...`:

- `retrieve_annotations_helpers.py:53` `match` (7 returns) — exists on
  master at `retrieve_annotations.py:43`.
- `named_signs.py:68,88` `of` / `of_name` (6 params) — exist on master in
  `sign_tokens.py`.
- `lemmatized_fragment_text.py:111` / `transliterated_fragment_lines.py:70`
  (46 duplicated lines) — the same block appears **twice inside master's
  `fragment.py`** (lines 349 and 567). The split moved one copy into each
  new file; qlty now reports it as 2 locations.

### 7. Sourcery finding triaged

Sourcery's only issue targets `text_line.py:151` (`merge` returning
`cast(L, TextLine.of_iterable(...))`). That file is **not in this PR's
diff** — `git diff origin/master...HEAD -- text_line.py` is empty. The
change landed on master through #740, which #743 was split out of. The code
is live but belongs to master, not to this PR. Additionally there are no
`TextLine` subclasses in the repo, so the unsoundness Sourcery describes is
not reachable today.

### 8. Data hard-gate check

Scanned every added line for multi-type containers. One hit:
`NameParts = Sequence[Union[ValueToken, BrokenAway]]` in the new
`sign_token_base.py`. Verified it exists verbatim on master
(`sign_tokens.py:67`) — relocated, not introduced. Flagged in the review
because the gate covers "any model you touch".

### 9. Test suite

`poetry run pytest` — **4251 passed, 2 skipped, 1 xfailed** in 318s.
(`task test-all` never reached this stage because `type-pyright` aborted it,
so the suite was run separately.)

### 10. Coverage on changed modules

`pytest --cov=<each changed source module> --cov-report=term-missing`:
2878 statements, **81 uncovered, 97%**.

Intersected every uncovered line with the diff's added-line ranges
(`git diff -U0 origin/master...HEAD`). Result: **no uncovered line in a
merely-modified file falls on a line this PR touched.** All 30 uncovered
statements attributable to the PR are in the four files it created:
`retrieve_annotations_helpers.py` 17, `chapter_manuscript_schemas.py` 7,
`token_base.py` 5, `sign_token_base.py` 1.

Confirmed the relocation is coverage-neutral by running the same targeted
test module in both trees:

- master: `retrieve_annotations.py` 146 statements, 31 missing (79%)
- branch: `retrieve_annotations.py` 14 + `..._helpers.py` 17 = 31 missing

qlty's own coverage check agrees: 95.9%, **+0.1% change**.

**Error made and corrected:** my first pass expanded coverage's
`term-missing` ranges arithmetically and reported 34 PR-attributable
uncovered lines. Coverage's ranges span non-statement continuation lines, so
that over-counted. The per-file `Miss` column (17 + 7 + 5 + 1 = 30) is the
authoritative figure and the review uses it.

### 11. Runtime verification (gate: run the service, exercise the route)

Safety, per the standing rule that `.env` points at the production cluster:

- `.env` was **never** sourced. `MONGODB_URI` was set explicitly to
  `mongodb://127.0.0.1:27017`, database `ebl_review_743_smoke`, dropped
  afterwards (verified via `list_database_names()` before and after).
- `create_app()` was called directly rather than `get_app()`, which would
  have initialised the production Sentry DSN.
- `AUTH0_PEM` was a freshly generated throwaway RSA key — no real credential
  was read.
- Served with waitress on `127.0.0.1:8123`.

Results:

- App booted; every route module registered.
- `GET /signs/transliteration/ku-nu-szi` -> 200 — ATF parser via the renamed
  `atf_grammar/` directory.
- `GET /markup?text=@i{italic} and plain` -> 200 with correct parts.
- `GET /fragments/query?transliteration=ku-nu-szi` -> 200 — exercises
  `TransliterationQueryText._create_signs`, i.e. the new `visitor.reset()`.
- `GET /fragments?random=true|needsRevision=true|interesting=true` -> 200 —
  the two-parameter `create_dispatcher` generics.
- `GET /fragments?bogus=1` -> 422 `DispatchError` — dispatcher error path.
- `GET /signs/transliteration/(((((` -> **500**. Traced to
  `signs.py:53` -> `get_unicode_from_atf` -> `parse_atf_lark`, where
  `TransliterationError` escapes unmapped. Confirmed **pre-existing**:
  `signs.py`, `mongo_sign_repository.py` and `error_handler.py` are untouched
  by this PR, and `check_errors` is textually identical to master. Reported
  as F10, out of scope.

In-process checks against the running tree:

- `SignsVisitor.reset()` clears `_standardizations` exactly as master's
  direct assignment did.
- `parse_line("1. ku-nu-szi")` round-trips; `atf_grammar/` exists and
  `lark_parser/` is gone.
- **`Museum` enum is byte-identical across the 3-way split** — all 72
  members, names, cities, countries and URLs diff clean against master.

**Errors made and recovered** while setting this up: the script imported
`Crypto` (the project uses `Cryptodome`), then failed with
`ModuleNotFoundError: No module named 'ebl'` because it lives outside the
repo. Fixed by correcting the import and setting
`PYTHONPATH=/workspaces/ebl-api`.

### 12. Public-surface check on the splits

Dumped `dir()` of each split module in both trees and diffed. Most losses are
incidental imports, but two modules lost names they defined themselves and
got no `__all__` facade — unlike `sign_tokens.py` and `enclosure_visitor.py`,
which did. Reported as F6.

### 13. Review file

Wrote `TASK-743-review.md` with the required sections: Summary, Findings,
Severity, Reproduction Steps, Recommendation. Ten findings (F1-F10), plus an
explicit disposition for every Sourcery and qlty item.

`task lint-md` — **0 errors** across all 13 markdown files. Six MD013
line-length errors in the review's tables were fixed by shortening the cells,
not by touching `.markdownlint.json`.

### 14. Cleanup

Removed the temporary `origin/master` worktree
(`git worktree remove --force`); `git worktree list` shows only the main
checkout. Dropped `ebl_review_743_smoke`. Working tree holds only the three
new `TASK-743-review*` files — no source file was modified, and **nothing was
committed**.
