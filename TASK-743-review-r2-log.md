# TASK-743-review-r2 — Work Log

Re-review of PR #743, requested by the user: fetch all reviews and
comments (sourcery-ai and every other agent and human reviewer), check
for failing checks, and check qlty issues.

## Entries

### 1. Read the copilot instructions

Read `.github/instructions/copilot.instructions.md` in full before
starting. Treating every section as a hard gate.

### 2. Identified the target PR

- `git branch --show-current` -> `fix-type-checker-blind-spots`
- `gh pr status` failed with a GraphQL permission error
  (`branchProtectionRule` not accessible by the integration token).
  Recovered by using `gh pr list --head <branch> --json ...` instead,
  which does not touch that field.
- PR is **#743**, "Make the ATF parser visible to the type checkers",
  `fix-type-checker-blind-spots` -> `master`, OPEN, not a draft.

### 3. Created the task tracking files

Created `TASK-743-review-r2-todo.md` and this log before starting
review work. Used the `-r2` id because `TASK-743-review*.md` files from
an earlier round already exist and are committed on the branch; a new
task gets its own files rather than reusing the previous task's.

Noted for the merge reminder: the branch currently carries committed
tracking files `TASK-743-fixes-*`, `TASK-743-merge-*`,
`TASK-743-review-*`, `TASK-743-size-*`, plus `TASK-743-review.md`.
These must be removed before the PR is merged.

### 4. Fetched all PR feedback

- `pulls/743/reviews` — 4 submitted reviews: sourcery-ai (COMMENTED, at
  `e3150b3d`), qltysh x2 (COMMENTED, at `19a2f464` and `aed3979f`),
  Fabdulla1 (**CHANGES_REQUESTED**, at `19a2f464`). `reviewDecision` is
  CHANGES_REQUESTED.
- `pulls/743/comments` — 10 inline comments: 1 from sourcery-ai
  (`text_line.py` merge cast), 9 from qltysh.
- `issues/743/comments` — 1, sourcery-ai's Reviewer's Guide.
- Sourcery's latest run was **skipped**: "your pull request is larger
  than the review limit of 150000 diff characters". So the only Sourcery
  finding is against the first commit and has not been re-reviewed.
- Also fetched feedback for the PRs the branch's master merge brought in
  (#740, #744, #745, #747, #748) per the review hard gate. All are merged
  with their findings resolved in master; none impose an open obligation
  on #743. Useful precedent: #740 was approved and merged carrying ~14
  unresolved qlty `function-parameters` / `similar-code` comments.

### 5. CI checks at head `aed3979f`

All green: Test Python 3.11 / 3.12 / pypy-3.11 success, GitGuardian
success, docker skipped, Sourcery skipped (size). Combined status
success, with `qlty check` reporting "8 blocking issues" in its
description.

### 6. Merge state

`gh pr view` reports `mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`
consistently across three polls. Locally, `git merge-tree --write-tree
HEAD origin/master` exits 0 and the `ort` result is clean, but the
legacy three-arg `git merge-tree` shows why GitHub disagrees:

- `docs/ebl-atf.md` — changed in both.
- `atf_parsers/lark_parser/ebl_atf_abbreviations.lark` — **modify/delete**:
  master's #749 added six manuscript types (`MultCol`, `Coll`, `StuTea`,
  `SchLen`, `Prism`, `Unc`) at the old path, which this branch deleted by
  renaming the directory to `atf_grammar/`.

Verified the `ort` merge carries #749's six types into
`atf_grammar/ebl_atf_abbreviations.lark`. A hand resolution that keeps
"our" file would silently drop them.

### 7. Gates run locally at `aed3979f` (clean tree)

- `task format` — pass, 831 files already formatted.
- `task lint` (ruff) — pass, all checks passed.
- `task type` (pyre) — **pass, no type errors**.
- `task type-pyright` — **FAIL: 19 errors, 1 warning.** Reproduced with
  the Taskfile's own pinned command
  (`npx --yes pyright@1.1.411` over `git diff --name-only
  --diff-filter=ACMR origin/master...HEAD -- '*.py'`). Confirmed pyright
  resolves the project venv (a probe file reports the fully typed
  `marshmallow.Schema.load` signature), so these are real, not
  unresolved-import noise. The PR description claims 0.
- `flake8 --max-line-length=120` on changed modules — pass.
- 250-line gate on all 77 changed `.py` files — pass.
- No new suppressions: the only `# noqa` in added lines (`B024`, `B027`)
  are pre-existing lines relocated from `tokens.py` into
  `token_base.py`.

### 8. Runtime verification (re-run against the current head)

`.env` was never sourced. Ran `create_app(create_context())` under
waitress on `127.0.0.1:8123` with `MONGODB_URI=mongodb://127.0.0.1:27017`,
throwaway db `ebl_review_743_r2_smoke`, a freshly generated throwaway
`AUTH0_PEM`, and `SENTRY_DSN` unset.

Error recovered: the first launch failed with `ModuleNotFoundError: No
module named 'ebl'` because the harness script lives outside the repo;
fixed by setting `PYTHONPATH=/workspaces/ebl-api`.

Results: `/signs/transliteration/ku-nu-szi` 200; `/signs/transliteration/$$$`
**422**; `/signs/transliteration/(((((` **422**; `/markup` 200;
`/fragments/query?transliteration=...` 200; `/fragments` with `random`,
`needsRevision`, `interesting` 200; `/fragments?bogus=1` 422.

In-process check of the `NamePart` rework on the running tree: `nameParts`
still serialises as interleaved `ValueToken`/`BrokenAway`, `NamePart`
never reaches the wire, `dump`/`load` round-trips to an equal object, and
`name` for `k[u]r` is `kur` — identical to master's
`isinstance`-filtered implementation.

### 9. Static review of the diff

Checked each dimension the review guidelines require.

- **Mixed-array hard gate.** `name_parts` moved from
  `Sequence[Union[ValueToken, BrokenAway]]` to `Sequence[NamePart]`.
  One type per array, classification done once in `NamePart.of`. Two
  separate arrays are not possible here — the interleaving of
  `ValueToken` and `BrokenAway` is the meaning of `k[u]r` — so the
  wrapper is the right call. Recorded as F10 so nobody "fixes" it later.
- **Probing.** `sign_unicode_lookup.extract_word_sub_indexes` still uses
  `getattr(part, "name_parts", [])` to decide whether a token is a
  `NamedSign`. Byte-equivalent to master, but the PR relocated it, and
  it is the source of two of the pyright errors. Finding F3.
- **Dead code.** No caller anywhere passes `start=` to
  `_StartParser.parse`; `MANUSCRIPT_PARSER` and `LINE_PARSER`, the only
  call sites that do pass `start=`, are raw `Lark` objects. The
  `__getattr__ -> object` proxy has no production consumer either — its
  only users are the three tests written to cover it. Finding F4.
- **Suppressions.** The only `# noqa` on added lines (`B024`, `B027`)
  are pre-existing lines relocated from `tokens.py` into
  `token_base.py`. No new `type: ignore`, `pyright: ignore`, `nosec` or
  `pragma: no cover`.
- **Coverage.** Intersected the `-U0` diff's added line numbers with the
  coverage report's missing lines across all 77 changed `.py` files:
  **0** uncovered PR-touched lines. The PR's claim holds.
- **mypy.** 5 errors over the changed set, all in untouched modules the
  changed files import (`atf_importer` package). Gate 8 as scoped to
  changed files passes.
- **flake8.** Clean. Fabdulla1's 169-character line at
  `annotations_service.py:140` does not raise E501 because pycodestyle's
  `maximum_line_length` exempts a comment of exactly `#` plus one long
  token. The Hilprecht line that was split was a string literal in a
  tuple — more than two chunks — so it did raise. Finding F5.
- **Sourcery's one finding is no longer in this diff.**
  `git diff origin/master...HEAD -- ebl/transliteration/domain/text_line.py`
  is empty; the `merge` cast reached master via #740 (`a238304d`).
  Finding F9.
- **qlty.** No local config, so `qlty smells` cannot run here. Checked
  all 9 bot comments by hand: every one is pre-existing code that a file
  split relocated. Finding F8.

### 10. Wrote the review

`TASK-743-review-r2-review.md`, 13 findings, template sections Summary /
Findings / Severity / Reproduction Steps / Recommendation.

Errors made and recovered while writing it: `task lint-md` failed twice
— first on MD013 (over-80 table rows) and MD036 (bold text used as a
heading), then on MD024 (duplicate `#### Reproduction steps` headings
introduced by the first fix). Resolved by converting the pyright table
to a bullet list, shortening the remaining table cells, and replacing
the bold/heading run-ins with a plain "Reproduce with:" line. Final run:
18 files, 0 errors.

### 11. Teardown

Stopped the waitress smoke server and dropped
`ebl_review_743_r2_smoke`. First `pkill -f "scratchpad/serve.py"`
attempt also matched the tool's own shell command line and killed it;
recovered by resolving the PID with `pgrep -f "serve\.py"` and killing
that.

### 12. Final state

Nothing was committed and nothing was pushed. The working tree holds
three new untracked files: `TASK-743-review-r2-todo.md`,
`TASK-743-review-r2-log.md`, `TASK-743-review-r2-review.md`. No source
file was modified.
