# TASK-735 Work Log — Review PR #735

## 2026-07-28

- Read `.github/instructions/copilot.instructions.md`; all gates in force.
- Identified PR #735 "Add GET /realia/all endpoint for listing Realia IDs"
  on branch `add-realia-slugs-endpoint` -> `master`.
  6 files changed, +215/-0, head `1f8e85e8`.
- Created `TASK-735-todo.md` and `TASK-735-log.md`.

### Feedback gathering (mandatory review gate)

- `gh api .../pulls/735/reviews` — 2 reviews: Sourcery `COMMENTED`
  (2026-07-03), Fabdulla1 `CHANGES_REQUESTED` (2026-07-22).
- `gh api .../pulls/735/comments` — 2 inline comments, both Sourcery.
- `gh api .../issues/735/comments` — 1, Sourcery Reviewer's Guide.
- GraphQL `reviewThreads` — 2 threads, both `isResolved: true`.
- `git log --merges master..HEAD` empty; branch is linear from
  `51ec7945`, so there is no merged-in branch PR whose feedback also
  needs fetching.
- Key observation: Fabdulla1's review post-dates the newest commit
  (2026-07-22 vs 2026-07-13), so it is unanswered.

### CI and qlty

- `gh pr checks 735` — 17 checks, all pass; `docker` skipped.
- qlty cloud: check "No blocking issues"; coverage 95.5% (+0.1%);
  coverage diff 100.0% vs 75% threshold.
- Local `qlty check --no-fail --upstream=master` — 14 issues:
  13 `bandit:B101` (asserts in tests, expected) and 1 `radarlint`
  `S1192` duplicated `"$ifNull"` literal at
  `mongo_realia_repository.py:109`.

### Local verification

- `task format` — 729 files already formatted, no unstaged changes.
- `poetry run pytest ebl/tests/realia --cov=ebl/realia` — 73 passed,
  100% coverage on every `ebl/realia` module, 0 missing lines.
- `poetry run flake8 <6 changed files> --max-line-length=120` — clean.
- `poetry run mypy <6 changed files> --ignore-missing-imports` —
  51 errors reported, all in transitively imported modules
  (`ebl/bibliography`, `ebl/corpus`, `ebl/ebl_ai_client.py`);
  zero in the files this PR touches. Pre-existing on `master`.
- `task type` (pyre, CI-enforced) — No type errors found.
- `wc -l` on changed `*.py` — max 246 (`test_realia_route.py`),
  all under the 250 hard cap but two test files are close.

### Behavioural probing

Wrote a temporary probe module into `ebl/tests/realia/`, ran it, and
deleted it (working tree confirmed clean afterwards). Results:

- Entry with 1 crossReference + `relatedTerms` + `type` + `wikidataId`
  -> `list_non_redirect_ids()` returns `[]`. Confirms Finding 2.
- 1 unresolvable `reallexikon` entry -> dropped; 2 -> kept.
  Confirms Finding 3.
- IDs `Zikkurat`, `Ähre`, `apsu`, `Adad` sort to
  `['Adad', 'Zikkurat', 'apsu', 'Ähre']`. Confirms Finding 5.
- With `_id == "all"` stored, `GET /realia/all` returns the ID list, not
  the entry. Confirms Finding 1.

### Review authored

- Wrote `TASK-735-review.md` using the required template: `Summary`,
  `Findings`, `Severity`, `Reproduction Steps`, `Recommendation`.
- Every prior finding explicitly dispositioned (2 Sourcery comments
  agreed as addressed, B101 acknowledged, Fabdulla1 unresolved).
- `task lint-md` — 0 errors after fixing 3 MD013 line-length violations.

### Result

Recommendation: **Request changes.** 2 blocking (High), 3 Medium,
3 Low findings.

- Reminder issued: remove `TASK-735-todo.md`, `TASK-735-log.md`, and
  `TASK-735-review.md` before merging.

## 2026-07-28 — Phase 2, addressing the findings

### Decisions taken with the user

- Findings 1 and 4: move the route to `/realia/ids`.
- Finding 5: accent- and case-insensitive sort (DIN 5007-1 style).
- Finding 3: drop the placeholder-count rule; approval given to move the
  "Has two reallexikon" case from the listable set to the stub set.

### Changes made

- New `ebl/realia/infrastructure/realia_stub_filter.py` — owns the
  `$expr` non-stub query. `OWN_CONTENT_ARRAY_FIELDS` now covers
  `afoRegister`, `references`, `afoCrossReferences`, `relatedTerms`,
  `type`, `wikidataId` (finding 2). `PLACEHOLDER_REALLEXIKON_COUNT` is
  gone (finding 3). `"$ifNull"` extracted as `IF_NULL` (finding 7).
- New `ebl/realia/infrastructure/realia_id_sorting.py` — `sort_realia_ids`
  sorts on an NFKD-decomposed, combining-mark-stripped, case-folded key
  with the original string as tie-break (finding 5). No new dependency.
- `mongo_realia_repository.py` — `list_non_redirect_ids` now delegates to
  both modules; file dropped from 217 to 157 lines.
- `bootstrap.py` — route moved to `/realia/ids` (findings 1 and 4).
- `realia.py` — `RealiaListResource.on_get` gains
  `@cache_control(["public", f"max-age={DEFAULT_TIMEOUT}"])` (finding 6).
- Tests split (finding 8): listing tests moved out of
  `test_realia_repository.py` (234 -> 151) and `test_realia_route.py`
  (246 -> 198) into new `test_realia_list_ids.py` (151) and
  `test_realia_ids_route.py` (75). The shadowing test is replaced by
  `test_entry_named_all_is_reachable`; new tests cover each content
  field, both reallexikon directions, ordering, tie-break, and the
  cache header.
- `.gitignore` — added `.claude/`, `CLAUDE.md`, `CLAUDE.local.md`,
  `.qlty/`. Verified with `git check-ignore -v`; both directories no
  longer appear in `git status`.

### Gates re-run

- `task format` — 2 new modules reformatted by ruff, then 733 files
  clean with no diff.
- `task lint` (ruff) — all checks passed.
- `poetry run pytest ebl/tests/realia` — 91 passed.
- `task test` — 3808 passed, 2 skipped, 1 xfailed, 0 failures.
- Coverage `--cov=ebl/realia` — 100%, 0 missing across 337 statements,
  including both new modules.
- `flake8 <10 changed files> --max-line-length=120` — clean.
- `mypy <10 changed files>` — 0 errors in changed files; the 51 reported
  errors are all pre-existing in transitively imported modules.
- `task type` (pyre) — No type errors found.
- `qlty check --upstream=master` — 20 issues, all `bandit:B101` asserts
  in test files; the S1192 finding is gone.
- `wc -l` — largest changed file 198 lines, well under the 250 cap.
- `task lint-md` — 0 errors.

### Phase 2 result

All eight findings resolved; `TASK-735-review.md` updated with a
resolution per finding. Changes are staged in the working tree but not
committed — awaiting the user's go-ahead.

Two contract changes to communicate on push: the endpoint path changed
from `/realia/all` to `/realia/ids`, and response ordering changed from
code-point to accent- and case-insensitive.

## 2026-07-28 — Phase 3, Pylance gate and frontend prompt

### Gap found

The user pointed out that pyright/Pylance had not been run. It is not
wired into the Taskfile and no `pyright` binary is installed, so it was
missed; ran it via `npx pyright@latest`.

### Pyright findings and fixes

5 errors across the changed files, all confirmed pre-existing on
`master` by running pyright in a temporary worktree checked out at
`master` (same code, shifted line numbers). Fixed anyway, since the
instructions do not accept pre-existing errors in changed modules:

- `mongo_realia_repository.py` `_load_entry` and `search`:
  `Schema.load` is typed as a union of unknown/list/dict/None, so
  passing the result to `_inject_bibliography(List[RealiaEntry])` and
  returning it were both errors. Wrapped in `cast`, matching the
  established pattern at `mongo_sign_repository.py:168,172`.
- `realia.py` `RealiaSearchResource.on_get`: falcon types
  `get_param` as `Optional[str]` even with `default=""`. Changed to
  `req.get_param("query", default="") or ""`, which makes the type true
  at runtime rather than asserting it. No behaviour change: the default
  is already `""` and `"" or ""` is `""`.

Pyright now reports 0 errors across all 10 changed files.

Left alone as out of scope: 102 pre-existing pyright errors in
`realia_schemas.py`, `test_realia_cross_references.py`, and
`test_realia_entry.py`. None of those files is in this PR's diff, and
fixing them would widen the change well beyond the review.

### Gates re-run after the phase 3 edits

- `task format` — one file reformatted by ruff, then 733 clean.
- `task lint` (ruff) — all checks passed.
- `flake8 --max-line-length=120` — clean.
- `mypy` — 0 errors in changed files.
- `pyright` — 0 errors across the 10 changed files.
- `task type` (pyre) — No type errors found.
- `poetry run pytest ebl/tests/realia --cov=ebl/realia` — 91 passed,
  100% coverage, 0 missing.
- `task test` — 3808 passed, 2 skipped, 1 xfailed.
- `qlty check --upstream=master` — 20 issues, all `bandit:B101`.
- `task lint-md` — 0 errors.

### Frontend prompt

Wrote `TASK-735-frontend-prompt.md`: a paste-ready prompt covering the
`GET /realia/ids` contract, the `Cache-Control` header, the fact that
IDs are German headwords needing URL encoding, the instruction not to
re-sort client-side (with a matching `Intl.Collator` comparator for the
cases that must), the warning that the list deliberately excludes
redirect stubs, the `/realia/all` migration note, required tests, and
acceptance criteria.

### Phase 3 result

Changed files are clean under mypy, pyre, and pyright. Still uncommitted,
awaiting the user's go-ahead.

## 2026-07-28 — Phase 4, root cause of the skipped gate

### Why pyright was skipped

Three layers failed, in order:

1. `.github/instructions/copilot.instructions.md` listed five pre-commit
   gates. Pyright was not among them — and neither was `task type`
   (pyre), even though CI is the thing that enforces pyre.
2. The stored project memory claimed `task type-pyright` existed and
   that `task test-all` ran it. Both were false: no such task was in
   `Taskfile.dist.yml`, and `test-all` ran only format, lint, type,
   test, lint-md. The memory read as coverage, so pyright was never
   sought out. Memories carry an explicit "verify before asserting"
   warning; that verification was not done.
3. Pylance diagnostics did reach this session twice, via the Edit tool's
   `ide_diagnostics` hook. Both were transient errors from half-applied
   edits of mine, and were dismissed as expected. Neither prompted a
   full-file check.

Running the members of `test-all` individually rather than the aggregate
also meant a missing member could not be noticed.

### Gate added

- `Taskfile.dist.yml` — new `type-pyright` task running
  `npx pyright@1.1.411` (pinned, matching how `lint-md` pins
  `markdownlint-cli2`). Defaults to Python files changed against the
  merge base with `master` **plus untracked files**; explicit paths can
  be passed after `--`.
- First version of the task used only `git diff`, which selected 4 of
  the 8 changed files and silently skipped every new file. Caught by
  checking its file list against `git status` before trusting the pass.
  Fixed by unioning in `git ls-files --others --exclude-standard`.
- Added `type-pyright` to `test-all`.
- Verified both directions: passes on the 8 changed files (0 errors),
  and fails with exit status 1 on a known-bad file
  (`realia_schemas.py`, 2 errors).
- Scope is changed-files, not repo-wide, because repo-wide pyright
  reports 1311 errors across 733 files (1007 of them under `ebl/tests`).
  A repo-wide gate would fail on day one.
- `.github/instructions/copilot.instructions.md` — pre-commit gate list
  extended with `task type` (pyre) and `task type-pyright`, plus a rule
  that a gate is not considered covered because an aggregate task or a
  prior session appeared to run it.
- Project memory corrected: it now records that the earlier version of
  itself was the cause of the miss, and that a task named in a memory
  must be verified against `Taskfile.dist.yml` before it is trusted.

### Phase 4 result

`task lint-md` — 0 errors. `qlty check` — 20 issues, all `bandit:B101`
in tests, unchanged.
