# TASK-743-r15-fix — Work Log

Records what was actually done, including every error and how it was recovered.

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` in full before acting.
- Created this log and `TASK-743-r15-fix-todo.md` before starting the work.
- Scope confirmed: R14-1 plus the non-blocking findings, and one PR comment on
  the two remaining blocking gates. No commit was requested and none will be made.

### R14-1 — stray files

- `git rm` removed all 34: 33 `TASK-*.md` plus `TASK-749-frontend.patch`.
  Against the staged tree, `git diff --diff-filter=A --name-only -M origin/master <tree>`
  filtered to non-`ebl/` paths returns **0**. The commit-based form in the PR
  description still reports 34 until the commit lands, because it compares
  commits rather than the working tree; that is now stated in the PR description.
- Patched the PR description via `gh api ... -X PATCH -F body=@file`
  (`gh pr edit --body` fails silently in this environment): Gate 3's count
  corrected from 28 to 34, with the cleanup's status spelled out.

### R14-4 — reassessed

- **Correction to the round-14 review.** R14-4 recommended naming the
  `copilot.instructions.md` change in the PR description "if it stays". It is
  already named, at line 348 of the description, with an explicit request that it
  be reviewed as a rules change. I missed that when reading the body. No edit was
  needed; the only open question is whether to split it into its own PR.

### R14-5 — applied with explicit approval

- Asked before touching it, because it deletes tests. Approval given for the full
  option. Removed `_StartParser.options`, the `LarkOptions` imports in both files,
  and `test_options_are_the_wrapped_parsers_options` and
  `test_an_uninitialised_wrapper_raises_attribute_error`.
- Error and recovery: ruff then failed with F401 — `_StartParser` was imported in
  `test_start_parser.py` only for the deleted test. Removed the import; ruff clean.

### R14-6 — the predicted failure mode was real

- Added `FACADE_SOURCES` (facade → the modules it was split into) and
  `test_facade_exports_every_name_it_re_exports`.
- It immediately found four names taken from split siblings but absent from
  `__all__`. One is a **genuine lost re-export**: `OrderedSignSchema` was a public
  class in `mongo_sign_repository` on `master`, moved to `sign_schemas`, and
  `from ebl.signs.infrastructure.mongo_sign_repository import *` no longer
  provided it. The other three (`get_unicode_from_atf`,
  `LEMMATIZED_FRAGMENT_TEXT`, `TRANSLITERATED_FRAGMENT_TEXT`) are new names used
  internally; exporting them costs nothing and makes the policy checkable.
- Mutation-checked: deleting `"ErasureState"` from `tokens.py`'s `__all__` now
  fails the new test and passes all three old ones — exactly the gap the finding
  described.

### R14-7 — invariant pinned

- Added `ebl/tests/transliteration/test_named_sign_alternation.py` (87 lines,
  48 cases over 16 broken-away ATF shapes).
- Mutation-checked twice: reversing the yield order in `NamedSign._interleaved`
  fails 18 cases; changing the legacy splitter's `[0::2]` to `[:1]` fails 9.
  Both restored afterwards.

### R14-10 — trailing newline

- Appended a newline to `ebl/fragmentarium/annotations.json`; still valid JSON.

### Errors made and recovered

- mypy flagged two annotations pyright had not seen, because `task type-pyright`
  scopes itself to files changed *in commits* and the new test file was untracked.
  Fixed `names: Set[str]` and `cast(TextLine, parse_line(atf))`, then ran pyright
  directly on the real changed set, where it found 5 further errors from
  marshmallow's `dump` return type. Added a typed `_dump` helper. All three
  checkers clean afterwards.
- The first coverage run was started before the last edits, making its evidence
  void under the re-verify gate. Killing it did not take effect cleanly and a
  second run overlapped with it; the shared output file then showed one failure,
  `test_atf_preprocessor.py::test_text_lines[...INANA...]`. Re-ran that file
  alone: 221 passed. Rather than assume the failure was the race, discarded both
  runs and started a single clean full run with a fresh output file.

### qlty — the one finding this round adds, and why it is justified

Measured, not assumed. `qlty smells --all --include-tests` at three points:

| Tree | Findings |
| --- | --- |
| `origin/master` (detached worktree) | 132 |
| pushed HEAD `a0b74092` | 107 |
| this working tree | 109 |

The two extra come entirely from `ebl/tests/factories/fragment.py`, whose
`__all__` grew by the two lines R14-6's rule requires. **Counterfactual run:**
removing just those two entries and re-running `qlty smells --all
--include-tests` returns **exactly 107**, byte-identical to the pushed HEAD's
finding set. So this is a re-pairing artefact of list length, not new duplicated
logic:

- `factories/fragment.py` `__all__` (24 lines) now shape-matches a list of ATF
  test strings in `test_transliteration/test_text_line.py` instead of the
  `PREFIXES` list in `test_museum_number.py`.
- That frees `test_museum_number.py` to pair with a list of test strings in
  `test_reconstructed_text_parser.py` — **two files this branch never touches**,
  whose lists were equally alike before and merely were not the chosen pairing.

Both are lists of unrelated string literals that happen to have the same AST
shape — precisely the carve-out the instructions name ("two unrelated `__all__`
lists that happen to have the same shape"). Nothing here can be removed without
either deleting a name the facade must export or deleting unrelated test data.

Nothing was silenced: no `qlty.toml` edit, no `# qlty-ignore`, no exclusion
pattern. qlty Cloud reports *No blocking issues* for this class, and the net
position against `master` is still **109 vs 132** — 23 findings lighter.

### Re-verification after the rewrites

- `task format` 913 files formatted · `task lint` clean · `task type` (pyre)
  **No type errors found** · pyright 0/0/0 · mypy clean · flake8 0 · lint-md 0.
- Full suite on the final tree: **4826 passed, 2 skipped, 1 xfailed, 0 failed**
  in 539.96 s. All 68 changed source files at 100% coverage; repo-wide 96.65%.
- Ran the service again on the final tree because `lark_parser.py` changed:
  `/signs/all` 200, `/signs?listAll=true` 200, `/signs/transliteration/ku` 200,
  `/signs/transliteration/[[[` 422, `/markup?text=@i{italic}` 200,
  `/markup?text=@i{unclosed` 422, `/signs?value=ku&subIndex=abc` 422 — all
  unchanged by the removal of `_StartParser.options`.

### Commit and comment

- Committed as `6e627647` "Close the round-14 review findings" — the 34
  deletions plus the six code changes. All nine pre-commit gates were run in
  order beforehand and recorded above; ggshield's secret scan hook passed.
- **Not pushed.** The commit authorization covered the commit only; the remote
  branch is still at `a0b74092`. Confirmed with `git ls-remote`.
- `git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'`
  now returns nothing — Gate 3 is closed on the branch.
- Posted one comment on PR #743 covering the two remaining blocking gates:
  <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743#issuecomment-5714853030>
  It states plainly that the cleanup commit is local and unpushed, so nobody
  reads the PR page and concludes otherwise.
- The six round-14 / round-15 task documents are deliberately left **untracked**,
  so that committing them does not reopen the very gate this round closed.

<!-- markdownlint-configure-file { "MD013": false } -->
