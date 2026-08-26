# TASK-743 — Review PR #743 — Work Log

## Task

Review PR #743 "Make the ATF parser visible to the type checkers".
User requirements beyond the standard review gates:

- Fetch all reviews and comments (sourcery-ai, other agents, humans).
- Check for failing checks and qlty issues.
- Warn on any dev container configuration change; check those very carefully.
- Verify no new `.md` files are present in the PR.
- Review doc: friendly, very short, human-looking summary section at the top,
  plus a `Details` subsection with every finding in full.
- Remove the line-length limit in the review document so it posts cleanly.

## Log

### Step 1 — Task tracking files created

Created `TASK-743-todo.md` and `TASK-743-log.md` before starting any review
work, per the task-tracking hard gate.

Identified the PR from the current branch `fix-type-checker-blind-spots`:
PR #743, base `master`, state OPEN.
Working tree was clean at start.

### Step 2 — PR metadata

PR #743, base `master`, head `b5d807ed`, 117 files, +5488/-3936.
`reviewDecision: CHANGES_REQUESTED` (Fabdulla1), `mergeStateStatus: BLOCKED`.
Merge base: `c2b0a5ef`.

### Step 3 — Feedback fetched (hard gate satisfied)

- `pulls/743/reviews` — 9 reviews: sourcery-ai (1 issue), Fabdulla1
  (CHANGES_REQUESTED, 5 points), 4x qltysh, 2x github-advanced-security.
- `pulls/743/comments` — 19 inline comments (sourcery, qlty, CodeQL).
- `issues/743/comments` — sourcery Reviewer's Guide + khoidt's reply.

### Step 4 — CI checks

All checks pass. `qlty check` annotated "1 blocking issue".
`qlty coverage diff` 100.0%. Total coverage 96.2% (+0.3%).

Open bot findings raised against the LATEST commit `b5d807ed`:

- qlty `function-parameters`: `named_signs.py:25` `_create` (count = 6).
- CodeQL 921/922 `Statement has no effect`: `legacy_transformer_base.py:38`
  and `:40`.

Both are REGRESSIONS of issue classes an earlier round of this PR had already
fixed (the `Logogram.with_surrogate` split for the parameter count, and the
`raise NotImplementedError` instead of `...` for the CodeQL alert).

### Step 5 — User-requested checks

- **Dev container configuration: NO CHANGES.** `git diff` over
  `.devcontainer/**`, `.github/**`, `Dockerfile*`, `docker-compose*`, `*.toml`,
  `*.ini`, `*.cfg`, `*.json`, `*.yml`, `*.yaml`, `Taskfile*`, `poetry.lock`
  is empty. Nothing to warn about; reported as such.
- **New `.md` files: NONE.** Only `docs/ebl-atf.md` is modified (grammar path
  rename). No `TASK-743-*.md` remain in the branch.

### Step 6 — Verified performance finding (nameParts serialization)

`token_schemas_signs.NamedSignSchema.name_parts` changed from
`fields.List(fields.Nested("OneOfTokenSchema"))` to
`fields.Function(_dump_name_parts, _load_name_parts)`, and both functions
build a fresh `OneOfTokenSchema()` (and re-execute a local import) on every
call, i.e. once per named sign.

Measured with `poetry run python`, dumping 200 `Reading` tokens through
`OneOfTokenSchema`, best of 3 x 30 runs:

- as merged (schema constructed per named sign): 83.14 ms
- module-level cached schema instance:           32.01 ms
- slowdown: **2.60x**; outputs byte-identical.

Reproduction script kept in the scratchpad. Filed as a finding.

### Step 7 — Gates run on the branch (head b5d807ed)

| Gate | Result |
| --- | --- |
| `poetry run ruff format --check ebl` | 843 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `task test` | 4379 passed, 2 skipped, 1 xfailed (306s) |
| `flake8 --max-line-length=120` (100 changed files) | exit 0 |
| `mypy --ignore-missing-imports` (100 changed files) | no issues in 100 files |
| `task lint-md` | 0 errors (after fixing my own TODO file) |
| 250-line limit | no changed `.py` file over 250 lines |
| >120-char lines | none in the changed set |

### Step 8 — Behaviour verification against the RUNNING service

Booted the real app (`ebl.app.create_app`) over HTTP on 127.0.0.1:8001 with
waitress, against a local throwaway Mongo database
(`mongodb://127.0.0.1:27017/`, db `ebl_review_743_scratch`). `.env` was NOT
sourced — it points at production.

Routes exercised (all as expected):

- `/signs/transliteration/kur` 200, `/signs/transliteration/$$$` **422**
  (the fix), erasure `ku°r\ru°` 200 (the round-2 regression stays fixed),
  `[k]ur` 200, `kur bad` 200
- `/signs/KUR` 200, `/signs/KUR/neoAssyrian` 200 (`find_signs_by_order`)
- `/signs?value=kur&subIndex=1` (+ homophones, + composite) 200,
  `/signs?listsName=HZL&listsNumber=1` 200
- `/markup?text=@i{italic}` 200
- dispatcher: `/fragments?random|interesting|needsRevision` 200,
  `/fragments?bogus=1` 422 (error path)
- `/fragments/query`, `/corpus/query`, `/texts`, `/provenances` 200

### Step 9 — Independent equivalence checks vs master (c2b0a5ef)

Used a `git worktree` at the merge base to run the same script both sides.

- **Museum enum**: 72 members, names and values **byte-identical** to master.
  Fabdulla1's five `PRIVATE_COLLECTION_*` 3-tuples are restored.
- **nameParts wire format**: `TextLineSchema().dump` over 20 ATF inputs
  (broken away, surrogate logograms, determinatives, erasures, compound
  graphemes) — **identical** to master.
- **Load round-trip**: dump -> load -> dump is stable and reconstructs the
  identical domain object for 7 representative inputs.
- **Tests**: 4381 collected on the branch vs 4293 on master; **zero** test
  function names present on master are missing on the branch.
- **`__all__` facades**: every name in every `__all__` is bound.

### Step 10 — Findings

Perf finding F1 reproduced with
`scratchpad/repro_nameparts_perf.py`: 2.65x, output byte-identical.

Checked and NOT a finding (verified, not assumed):

- `MemoizingSignRepository.search_composite_signs` narrowing `sub_index` to
  `int` matches the ABC, which already declared `int`.
- `LINE_PARSE_ERRORS` is exactly the old inline
  `(*PARSE_ERRORS, TransliterationError, ExtentLabelError)`.
- `prepare_reconstruction` == `pydash.flow(set_enclosure_type, set_language)`.
- `ManuscriptLine._update_omitted_words` is equivalent to the old comprehension.
- `retrieve_annotations_helpers.match` is equivalent to master's 7-return form.
- `File.content_type` -> `Optional[str]` matches what GridFS already returned.
- `MongoCollection.find_one` raises `NotFoundError` on a miss, so the new
  `cast(Dict[str, Any], ...)` in `query_manuscripts_by_chapter` is safe.
- `# noqa: B024/B027` in `token_base.py` were carried over from master, not new.
- The bare `visited_parts: Sequence` annotations are NOT hiding a checker
  error: removing them keeps pyright and mypy at zero on that file.

### Step 11 — Coverage (first attempt failed, corrected)

**Error made:** I built the `--cov` argument as
`--cov="$(echo $SRC | tr ',' ' ' | sed 's/ / --cov=/g')"`, which collapses the
whole list into a single quoted `--cov` value containing spaces. pytest
accepted it, measured nothing, and printed an empty coverage table after a
10-minute run.

**Recovery:** re-ran as `pytest --cov=ebl --cov-report=` and reported on the
changed files afterwards with `coverage report --include=...`, plus a
line-level diff-coverage check against `git diff` for lines this branch adds
or modifies.

### Step 12 — Review document

Wrote `TASK-743-review.md` with, in order: a short friendly review summary,
a `Details` subsection carrying every finding in full, then the required
template sections (Summary, Findings, Severity, Reproduction Steps,
Recommendation).

Per the user's explicit request the line-length limit is removed **for that
document only**, via an inline `<!-- markdownlint-disable MD013 -->` at the
top. No linting configuration file was created or modified — there is no
`.markdownlint.json` in this repo and `.markdownlintignore` is untouched.

`task lint-md` initially reported one MD036 error (`**Severity: Info**` read
as an emphasis-heading); fixed by making it plain text. Now 0 errors.

### Step 13 — Coverage (corrected run)

`poetry run pytest --cov=ebl --cov-report=` — 4379 passed, 2 skipped,
1 xfailed (567 s), then `coverage json` plus a line-level diff-coverage
script (`scratchpad/diff_coverage.py`) that intersects the `+` hunks of
`git diff -U0 c2b0a5ef..HEAD` with `missing_lines`.

Result: **100 files with added/modified Python lines, 1128 executable lines
added or modified, ZERO uncovered.**

Twenty touched files are below 100% overall. I checked the hunk ranges for
the two worst (`retrieve_annotations.py` 79.41%, `tokens.py`) and confirmed
their missing lines fall outside every `+` hunk — pre-existing gaps on lines
this PR does not touch. None of the twelve newly created modules has an
uncovered line, so every relocated line is covered.

### Step 14 — Cleanup

Killed the review web server, dropped the throwaway Mongo database, and
removed the temporary `git worktree` at the merge base. Verified the working
tree contains only the three TASK-743 files.
