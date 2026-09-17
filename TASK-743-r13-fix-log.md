<!-- markdownlint-disable MD013 -->
# TASK-743-r13-fix — Work Log

Addressing the round-13 review findings on PR #743.

## 2026-09-16

### Step 0 — gates re-read

Re-read `.github/instructions/copilot.instructions.md` before starting. Two
points bind immediately:

- B2 ("resolve the conflict with master") requires `git merge` or `git rebase`.
  The user asked me to "address all the findings"; that is **not** a request for
  a merge or rebase in their own words. Per the hard gate, approval is
  single-use and never inferred from momentum or from the work being obviously
  needed. I will do everything else and ask.
- B1 deletes 23 tracked files including `TASK-743-review.md`, the review itself.
  Confirming scope before deleting.

### Step 1 — task files created before any work

- `TASK-743-r13-fix-todo.md`, `TASK-743-r13-fix-log.md`.

### Correction carried over from the review task

The round-13 coverage cross-check I reported as "still running" collected **no
data**: I passed `--cov=ebl/.../file.py` (a file path), and coverage emitted
`module-not-imported` for all five modules followed by `No data was collected`.
The 3092 tests passed but measured nothing. My invocation error, not a project
problem. Redone correctly in step 6 below.

### Step 2 — B3, the 500 that should be a 422

- Checked layering first: `ebl/errors.py` imports nothing, and two domain modules already raise `DataError` (`transliteration_query.py`, `corpus/domain/parser.py`). So raising it from `sign_token_base.py` follows the existing pattern rather than inventing one.
- Checked every `except ValueError` site in non-test code (20 of them). None sits in the named-sign construction path — `LineNumberString` is line numbers, `ValueEnumField` is enums — so switching the exception class cannot be swallowed anywhere.
- Changed all three validators in `sign_token_base.py` to raise `DataError`: `_validate_sub_index`, `_validate_name_parts`, `_validate_name_breaks`. `DataError` is already mapped to 422 in `error_handler.py`.
- Did all three, not just `name_breaks`: `_validate_sub_index` had the same defect and I said in the review that fixing them together was natural. `_validate_name_parts` is the same class of data error.
- **Three existing tests asserted `ValueError`** and now assert `DataError`
  (`test_named_sign_validation.py:16`, `test_named_sign_name.py:62` and `:88`).
  No test was removed, disabled or skipped — the assertion was updated to match a
  deliberate contract change, which is the whole point of the fix.
- File is 180 lines, under the 250 gate.

### Step 3 — N1, the shim's implicit contract

- `name_breaks` changed from `load_default=()` to `required=True` in `NamedSignSchema`, so the schema now states what the shim already assumed: an absent `nameBreaks` means the legacy interleaved format, and a new-format payload must send the key.
- **Honest note on what this does and does not fix.** The pre-load shim still runs first and injects `nameBreaks`, so a payload with two `nameParts` and no `nameBreaks` is still split and still 422s. I checked whether that is wrong and it is not: `[ValueToken, ValueToken]` is invalid *legacy* too (legacy always alternates), so 422 is the correct status under either reading. What changes is that the declared contract now matches the behaviour. The error message still describes the split rather than the missing key; I did not chase that further because the alternative — inspecting the array's contents to guess its format — is exactly the probing the data hard gate forbids.
- File is 204 lines, under the gate.

### New tests

- `ebl/tests/transliteration/test_named_sign_errors.py`, 5 tests, 83 lines:
  - breaks > parts raises `DataError` (not `ValueError`)
  - breaks > parts is **422 on a real falcon route**, through the real `error_handler.set_up`
  - a negative `subIndex` is 422 on a route (the pre-existing 500, now fixed)
  - an absent `nameBreaks` is read as legacy, pinning the contract N1 makes explicit
  - `nameBreaks` is reported as required when `nameParts` cannot be separated
- Put in a new file rather than appended: `test_named_sign_name.py` is already 212 lines and would have crossed the 250 gate.
- `ebl/tests/transliteration` + `test_error_handler.py`: **1770 passed**, 1 skipped, 1 xfailed.

### Steps 4–8 — verification after the rewrite (previous evidence treated as void)

- **ATF equivalence probe re-run** against the fixed tree: still **byte-for-byte identical** to the merge-base baseline across all 60 cases. The fixes change error classes and one schema flag, not parser output.
- **Coverage, correct invocation this time** (`--cov=ebl.transliteration.domain.sign_token_base` as a module, not a file path):

  ```text
  ebl/transliteration/application/token_schemas_signs.py   80   0   100%
  ebl/transliteration/domain/sign_token_base.py            92   0   100%
  TOTAL                                                   172   0   100%
  ```

- **qlty repo-wide**, `--all --include-tests`: **106 findings, identical to the pre-fix tree**. Diffed both ways: nothing introduced, nothing removed. The new test file trips no `similar-code`.
- **Service re-booted against the fixed tree** (fresh db `ebl_t743_r13b`) and the routes re-exercised:

  | Route | Before | After |
  | --- | --- | --- |
  | `GET /fragments/K.3` (breaks > parts) | **500** | **422** ← B3 fixed |
  | `GET /fragments/K.1` (legacy interleaved) | 200 | 200 |
  | `GET /fragments/K.2` (non-alternating legacy) | 500 | 500 (unchanged — see below) |
  | `GET /signs/transliteration/kur` | 200 | 200 |
  | `GET /signs/transliteration/$$$` | 422 | 422 |
  | `GET /signs?listAll=true` | 200 | 200 |
  | `GET /markup` valid / invalid | 200 / 422 | 200 / 422 |

- **N2 deliberately left as code.** K.2 still 500s. I checked whether to map it and decided not to: `mongo_fragment_repository_get.py` loads every stored fragment through the schema, so a marshmallow `ValidationError` on unreadable stored data is the repository's existing behaviour for all documents, not a new defect class this PR introduces. Turning it into a 422 would mean telling a client their request was bad when the database is what is wrong. N2's remedy stays what the review said: state the deploy order, and rely on #764's `NonAlternatingName` to find such documents before deploy.

### Gate results on the fixed tree

| Gate | Result |
| --- | --- |
| `ruff format --check ebl` | 887 files already formatted |
| `ruff check ebl` | All checks passed |
| **pyre** (`poetry run pyre check`) | **No type errors found** |
| pyright (direct, on the changed files) | 0 errors, 0 warnings, 0 informations |
| flake8 (changed, 120 cols) | exit 0 |
| mypy (changed) | Success, no issues |
| qlty (changed + repo-wide) | no new findings |

### Errors made and recovered

1. **Pyre reported failure on the first run** — `Pyre encountered an internal exception: End_of_file`, exit 2. That was resource contention with a pytest coverage job running at the same time, not a type error. Re-ran with nothing else running: **No type errors found**. Recorded rather than quietly re-run, because a red CI gate is not something to paper over.
2. **`task type-pyright` did not check my work.** The task computes `git diff --diff-filter=ACMR "$BASE...HEAD"` — that is *committed* changes against `origin/master`. My changes are uncommitted, so the task passed while checking none of them. Re-ran pyright directly on the five changed files, which found **6 real errors** in the new test file (`ReadingSchema().load()` is typed `Any | list | dict | None`, so `.name_parts` is unknown). Fixed with `cast(Reading, ...)` — matching how `test_named_sign_name.py` already handles it — not with a suppression, since "no `# type: ignore`" is this PR's own claim. Clean afterwards.
3. Earlier, in the review task, I measured coverage with `--cov=<file path>.py` and got `No data was collected` while the tests passed. Fixed by passing dotted module paths.

### Step 9 — answers received, B2 merge (explicitly authorized)

The user answered: **merge `origin/master` in**; leave B1's artefacts until merge time; update the PR description and resolve the Sourcery thread. They did **not** pick re-requesting review, so N5 is left alone.

- Recorded the remote head first (`549d45ae`), because a commit in this repo has previously reached GitHub with no `git push` run.
- Checked overlap before merging: master changed 58 files since the merge base, **none** of them files I had modified, so the dirty working tree was safe.
- `git merge origin/master --no-edit` → one conflict, `ebl/fragmentarium/domain/museum.py`, exactly as the review predicted.
- **The conflict is structural, not textual.** The branch moved museum entries out into `museum_entries_a_l/m_s/t_y.py` and left the enum holding references; master added three museums inline (`ERIMTAN_MUSEUM`, `GAZIANTEP_MUSEUM`, `KAHRAMANMARAS_MUZESI` — from #765 and #766). Resolved by keeping the branch's structure and adding master's three museums *in that structure*: entries appended to `museum_entries_a_l.py` in alphabetical position with the `MuseumEntry` annotation, enum members referencing them in master's ordering.
- **Verified the resolution rather than eyeballing it.** Built the `Museum` enum in three worktrees and compared `{name: [museum_name, city, country, url]}`:
  - merged vs `origin/master`: **identical** — 75 members, identical values.
  - merged vs branch `549d45ae`: added `ERIMTAN_MUSEUM`, `GAZIANTEP_MUSEUM`, `KAHRAMANMARAS_MUZESI`; **nothing removed, nothing changed**.
- `museum_entries_a_l.py` is 193 lines and `museum.py` 115 — both under the 250 gate.
- `poetry.lock` and `pyproject.toml` moved in master; `poetry install --no-root` reported nothing to update, so the environment already matched.

### Gates before completing the merge commit

Run on the merged tree, which also carries my uncommitted B3/N1 fixes — a superset of what the merge commit contains:

| Gate | Result |
| --- | --- |
| `ruff format --check ebl` | 912 files already formatted |
| `ruff check ebl` | All checks passed |
| **pyre** | **No type errors found** |
| pyright (direct, on changed + resolved files) | 0 errors, 0 warnings, 0 informations |
| mypy | Success, no issues in 5 source files |
| flake8 (120 cols) | clean |
| `task lint-md` | 0 errors over 30 files |

### PR description updated (N2, N3, N4 + the Gate 3 command)

Patched via `gh api repos/.../pulls/743 -X PATCH -F body=@file` — `gh pr edit --body` fails in this repo (deprecated Projects GraphQL). Confirmed applied: `updated_at` 2026-09-16T16:57:41Z, body 36914 chars.

- **N3** — replaced the gate table's `qlty smells | 0 findings in any file this PR touches` with the reconciled figure: 2 accepted `similar-code` findings, repo-wide 126 → 106.
- **N4** — the round-5 claim "the `nameParts` wire format is unchanged" is now marked **Superseded**, pointing at the breaking-change notice at the top. It was contradicting line 6 of the same description.
- **N2** — Gate 2 now states the deploy order explicitly: dry-run #764's migration **before** merging this PR, because `NonAlternatingName` is what proves no un-splittable document exists; then merge; then apply.
- **Gate 3 command** — it covered `TASK-743*`/`744*`/`745*` (12 files) when there are 23. Corrected to `git rm 'TASK-*.md' TASK-749-frontend.patch`, with the reviewer's verification query and a note that #764 needs the same for its 14 files.
- Added a "Part 13 — round-13 review follow-ups" section recording the merge, B3, N1, the tests and the description corrections.

### Sourcery thread resolved

`PRRT_kwDOCBABsM6TT-qP` (`text_line.py`, the `merge` cast) resolved via the GraphQL `resolveReviewThread` mutation — confirmed `isResolved=true`. `@final` on `TextLine` answered it structurally.

The two `qltysh` threads (`tests/factories/fragment.py`, `transliteration/domain/tokens.py`) were **left open deliberately**: they are the accepted-with-justification duplications, and leaving them visible is more honest than resolving them. The user asked only for the Sourcery thread.

### Not done, and why

- **B1** — the user chose to leave the 23 task artefacts until merge time. The corrected `git rm` command is now in the PR description so it is right when the time comes. Nothing deleted.
- **N5** — re-requesting review was offered and not selected. Untouched.
- **N6** — #764's 14 `TASK-764-*.md` files are on another branch; noted in the PR description rather than changed from here.
- **I1** — pre-existing mixed arrays, explicitly no action requested in the review.

### Step 10–11 — merge commit and final state

- Full suite on the merged tree: **4773 passed, 2 skipped, 1 xfailed**, exit 0.
- qlty on the merged tree: **106 findings, same count as before the merge**; zero on the two files the resolution touched. (I could not diff finding-for-finding: the pre-merge baseline file was lost when the scratchpad was cleared between sessions. Count equality plus a clean run on the resolved files is what I actually have.)
- Verified the staged set before committing: **none** of `sign_token_base.py`, `token_schemas_signs.py`, the test files or any `TASK-*` file was staged, so the merge commit contains the merge alone.
- `git commit --no-edit` → `5935b154`. ggshield pre-commit secret scan passed.
- **Checked the remote immediately afterwards**, because this repo has previously had a commit reach GitHub with no `git push`: `git ls-remote` still returns `549d45ae`. **It did not auto-push this time.** Local is 8 commits ahead (the merge plus master's seven).
- `TASK-743-review.md` updated with a Resolution section and a corrected verdict row; `task lint-md` clean over 30 files.

### Final state

- Local `HEAD` `5935b154` — merge commit only.
- **Uncommitted** in the working tree: the B3 and N1 fixes, the three updated tests, the new `test_named_sign_errors.py`, and the task/review markdown.
- **Nothing pushed.** The PR page still describes `549d45ae`, so its mergeability and check verdicts are stale relative to the local tree.
- Commits made this task: exactly one, the merge the user explicitly asked for. No push, no rebase, no force, no history rewrite.

## 2026-09-17 — documentation, handoff and commit

- Wrote `TASK-743-r13-handoff.md`: current state, what round 13 fixed, the five open items with the two blocking ones marked, an ordered next-steps list, and the traps (the `task type-pyright` blind spot, spurious pyre `End_of_file`, `qlty --include-tests`, `gh pr edit` failing here, `.env` pointing at production, commits reaching GitHub without a push).
- **Counted the artefacts honestly.** The branch carried 23 root artefacts; this commit adds five more task/handoff documents, so it is now **28**. Updated `TASK-743-review.md`'s B1 row and the PR description to say 28 rather than 23. The `git rm 'TASK-*.md'` glob in the cleanup command already covers the new files, so the command itself did not need changing — only the number beside it.
- Re-ran every pre-commit gate before committing rather than trusting the earlier runs, since the user has now asked for a commit.
