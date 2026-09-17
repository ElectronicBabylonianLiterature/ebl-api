<!-- markdownlint-disable MD013 -->
# TASK-743 — Handoff after round 13

PR [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743), branch `fix-type-checker-blind-spots` → `master`.

Written for whoever picks this PR up next. It says where the branch stands, what is left, and what to do in what order.

## Where things stand

| | |
| --- | --- |
| Local `HEAD` | `5935b154` — merge of `origin/master`, plus this commit |
| Remote branch | was `549d45ae` before this commit; **check `git ls-remote` before assuming anything is unpushed** |
| PR page verdicts | describe `549d45ae`. **Stale** until the branch is pushed |
| Mergeability on GitHub | still shows conflicted until the merge is pushed |
| Local gates | all green — see the table at the bottom |

## What this PR does, in plain words

A module and a directory shared the same dotted name, so the ATF parser was invisible to the type checkers. Nobody had been checking it. This PR makes it visible and fixes everything that surfaced once it was.

The one change that affects data: a sign's name used to be stored in a single `nameParts` array holding two different kinds of thing — the letters and the broken-away brackets, mixed together. They are now two separate arrays, `nameParts` and `nameBreaks`. That is a wire-format change and a stored-shape change.

## What was fixed in round 13

- **The merge conflict.** `master` had added three museums (`ERIMTAN_MUSEUM`, `GAZIANTEP_MUSEUM`, `KAHRAMANMARAS_MUZESI`) straight into `museum.py`, while this branch had moved every entry out into `museum_entries_a_l/m_s/t_y.py`. Resolved by keeping this branch's structure and putting master's three museums into it. Verified by building the `Museum` enum on all three sides and comparing every field: identical to `origin/master` (75 members), and only those three added relative to the branch.
- **A 500 that should have been a 422.** Sending a malformed `nameBreaks` array crashed with a server error instead of telling the client their data was wrong. The three validators in `sign_token_base.py` now raise `DataError`, which is already mapped to 422. This also fixed the same bug for a negative `subIndex`, which predated this PR.
- **An untruthful schema.** `nameBreaks` said it was optional while the compatibility adapter treated its absence as "this is the old format". It is now `required`, so the schema says what the code does.
- **Five new tests** in `ebl/tests/transliteration/test_named_sign_errors.py`, including two that check the 422 on a real route through the real error handler. Three existing tests moved from `ValueError` to `DataError` to match the new contract. None was removed, skipped or disabled.
- **The PR description**, on four counts: a stale qlty row, a passage that contradicted the breaking-change notice, the missing deploy order against #764, and a cleanup command that named 12 files when there were 23.
- **The Sourcery review thread** on `text_line.py` — `@final` on `TextLine` had already answered it structurally.

## What is still open

### 1. The branch is not pushed

Everything above is local. Until it is pushed, the PR still shows the conflict and the old check results, and no reviewer can see any of it.

### 2. The task documents must not reach `master` (blocking)

The branch carries task-tracking markdown and one `.patch` file at the repository root. **This commit adds five more**, so the count is now **28**, not the 23 the description mentions. They are committed so the history is reviewable, not because they belong in the codebase.

```bash
git rm 'TASK-*.md' TASK-749-frontend.patch
```

Then confirm it comes back empty:

```bash
git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'
```

The glob covers the new files too, so the command in the PR description is still correct — only its stated count is now low.

**#764 needs the same** for its own 14 `TASK-764-*.md` files.

### 3. The migration must be dry-run before this merges (blocking)

The migration lives in **#764**, not here. Order matters:

1. **Dry-run #764's migration against production first.** It stops with `NonAlternatingName`, naming the collection and `_id`, on any old `nameParts` array that does not alternate letter, bracket, letter. Such a document reads fine on `master` but **cannot** be read once this PR ships, because the adapter separates the array by position. A clean dry run is the proof that no such document exists.
2. Merge this PR, so the adapter is deployed and old documents keep loading.
3. Apply #764's migration.

### 4. The approval is stale

`Fabdulla1` approved on 2026-09-01 at `16a84e20`. Everything they asked for is fixed, but a lot has landed since, including the array split itself. Worth re-requesting. This was offered and deliberately not taken, so it is a decision, not an oversight.

### 5. Smaller things, nobody is blocked on them

- **A pre-existing mixed array.** `manuscript_line.paratext` is `Sequence[Union[DollarLine, NoteLine]]` and uses an `isinstance` probe to tell them apart — the same defect this PR spent 26 commits fixing for `nameParts`. Untouched here and out of scope, but the obvious next candidate.
- **Two accepted qlty findings.** Both are lists of bare strings that happen to look alike (`__all__` against `__all__`, and `__all__` against a list of museum-number prefixes). Nothing to extract. Justified in the PR description, and their threads were left open on purpose so the justification stays visible.
- **An error message.** A payload with two `nameParts` and no `nameBreaks` returns 422, which is correct — it is invalid as old format too — but the message describes the split rather than the missing field. Improving it would mean inspecting the array's contents to guess its format, which the data rules forbid. Left alone on purpose.

## Next steps, in order

1. Push the branch.
2. Wait for CI, qlty and CodeQL to re-run against the merge.
3. Dry-run #764's migration against production; confirm it reports nothing.
4. Re-request review.
5. Immediately before merging: `git rm 'TASK-*.md' TASK-749-frontend.patch` on both this branch and #764, and confirm the verification query is empty.
6. Merge this PR, then apply #764's migration.

## Traps worth knowing

- **`task type-pyright` only checks committed files.** It diffs `origin/master...HEAD`, so uncommitted work passes without being looked at. Run `npx pyright@1.1.411 <files>` directly while iterating. This hid six real errors in round 13.
- **Pyre can fail spuriously.** An internal `End_of_file` under CPU contention looks like a broken gate. Re-run with nothing else going; it was clean both times afterwards.
- **`qlty smells` silently skips test files without `--include-tests`**, and a changed-files run cannot see a duplication against an untouched file. Use `--all --include-tests` and compare against a base worktree.
- **`gh pr edit --body` fails in this repo.** Patch the description with `gh api repos/.../pulls/743 -X PATCH -F body=@file`.
- **Never source `.env` for local runs** — it points at the production cluster. Use `mongodb://127.0.0.1:27017`.
- **A commit here has reached GitHub without a `git push`.** Always check `git ls-remote` before claiming anything is unpushed.

## Gate results at this commit

| Gate | Result |
| --- | --- |
| `task format` | clean |
| `task lint` (ruff) | passed |
| `task type` (**pyre**, the gate CI enforces) | **No type errors found** |
| pyright, run directly on the changed files | 0 errors, 0 warnings, 0 informations |
| `task test` | **4773 passed**, 2 skipped, 1 xfailed |
| Coverage | `sign_token_base.py` and `token_schemas_signs.py` both **100%** |
| `flake8 --max-line-length=120` | 0 errors |
| `mypy --ignore-missing-imports` | 0 errors |
| `qlty smells --all --include-tests` | 106 findings, unchanged by this work; 2 accepted, both justified |
| `task lint-md` | 0 errors |
| ATF equivalence probe, 60 cases | byte-for-byte identical to the merge base |
| Running service | legacy fragment 200; malformed `nameBreaks` 422 (was 500); `/signs/transliteration` 200 / 422 |
