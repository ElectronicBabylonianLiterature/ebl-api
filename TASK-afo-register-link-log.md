# TASK afo-register-link — Work Log

Records what was actually done, including every error and its recovery.

## Task

`POST /afo-register/texts-numbers` returns `[]` for AfO references whose
`text` or `textNumber` contains a space, breaking the Fragment → AfO link.
Reported case: `["OrNS 59, 17"]` on fragment MNAO.11676.

## Entries

### 1. Task tracking created

Created `TASK-afo-register-link-todo.md` and this log before starting work,
per the task-tracking hard gate.

Noted: the ten `TASK-config-*` / `TASK-devcontainer-*` untracked files present
in the session-start git status no longer exist on disk. Flagged to the user;
nothing to remove.

### 2. Branch created

`fix-afo-register-texts-numbers-split` from `origin/master` (fetched fresh).

### 3. Reproduced against production before changing anything

- `["OrNS 59, 17"]` → `[]` (bug confirmed).
- `["AfO 17,257ff."]` → 1 record (`text="AfO"`, `textNumber="17,257ff."`).

Confirms the prompt's diagnosis: `rsplit(" ", 1)` on `"OrNS 59, 17"` yields
`("OrNS 59,", "17")`, which matches no document.

### 4. Read the code

`_build_indexed_query` splits each query via `split_text_and_number` and only
returns `None` — falling through to the correct `_build_fallback_pipeline`
concat match — when a query fails to split. Broken inputs split
"successfully" into the wrong pair, so the fallback is never reached.

Observations made while reading, beyond the prompt:

- The `isinstance(query, str)` guard in `split_text_and_number` was already
  dead: `search_by_texts_and_numbers` normalised with `query.strip().split()`
  before calling it, so a non-string raised `AttributeError` first. Removing
  the function drops the dead guard without changing behaviour.
- The old code was all-or-nothing: one unsplittable query sent *every* query
  to the concat pipeline.

### 5. Implemented the preferred fix

`candidate_splits` enumerates every space position; `_build_candidate_query`
`$or`s all candidates across all queries. Equivalent to the concat match
because `text + " " + textNumber == query` holds iff some space position
splits `query` into that exact pair — while still using the compound
`(text, textNumber)` index.

Design points:

- Normalisation kept, moved into `candidate_splits`. Because the normalised
  string has no leading/trailing/repeated spaces, every candidate has a
  non-empty `text` and `textNumber` — no empty-side candidates to filter.
- Empty `$or` is a Mongo error (`$or must be a nonempty array`), so
  `_build_candidate_query` returns `None` and the search returns `[]` when no
  query contains a space. This also subsumes the old `if not query_list`
  guard, which is now removed rather than left as a second unreachable branch.
  A space-free query could never match a concat that always contains a space,
  so returning `[]` preserves the old behaviour exactly.
- `_build_fallback_pipeline` deleted: the `$or` path is provably equivalent,
  making the pipeline unreachable dead code (the 100% coverage gate would
  flag it regardless).

### 6. Tests added

Repository level: space in `text_number`; spaces in both fields; partial-match
rejection (`"A B C D"` vs `text="A B"`, `text_number="C"`); batch mixing
spaced and unspaced; empty query list; space-free query. Route level:
`["OrNS 59, 17"]` returns only the matching record. The two existing tests
(`test_search_by_texts_and_numbers`,
`test_search_by_texts_and_numbers_with_spaces`, including its
`"  Text With Space   4  "` normalisation coverage) pass unchanged.

Also added `test_find_by_quoted_text_number_matches_exactly`: coverage showed
line 25 of the changed file (the quoted exact-match branch of
`create_search_query`) uncovered, with no test anywhere in the suite hitting
it. Pre-existing gap in a file this task touches, so filled rather than
preserved.

### 7. Error made: format gate failed

`task format` (`ruff format --check`) rejected the test file. Recovered by
running `poetry run ruff format ebl/tests/afo_register/`. Note `task format`
in this repo is check-only despite the gate wording "auto-format"; the
formatter must be run separately.

### 8. Error made: flake8 E203 vs ruff format — rewrote the implementation

First implementation sliced by space index:
`normalized_query[index + 1 :]`. `ruff format` demands that spacing; flake8
flags it `E203 whitespace before ':'`. Contradictory checkers, and config
changes / ignore comments are forbidden — so per the instructions the code
was wrong, not the checkers. Restructured to tokens:

```python
tokens = query.strip().split()
[(" ".join(tokens[:index]), " ".join(tokens[index:])) for index in range(1, len(tokens))]
```

Equivalent (`str.split()` on whitespace runs then `" ".join` reproduces the
normalised string exactly, and token boundaries are exactly its space
positions), satisfies every checker, and folds normalisation into the same
step. This is a better design, as the instructions predict.

### 9. `task type-pyright` does not exist

Gate 4 names `task type-pyright`; this Taskfile defines no such task, and
`pyright` is absent from the venv, `pyproject.toml`, `package.json` and the
CI workflows. Did not skip the gate — ran pyright directly via
`npx pyright@latest` on the changed files.

It reported 2 errors (marshmallow `load()` union passed to
`cast_with_sorting`), one in `search` and one in `search_by_texts_and_numbers`.

Error made: first attempt to check whether these pre-existed on `master`
used `cd` into the scratchpad plus `grep -c`, which broke path resolution and
wrongly reported 0. Re-ran from the repo root and confirmed **master has the
same 2 errors** — pre-existing, not introduced here.

Both sit in a file this task touches, and the instructions state a
pre-existing error in a touched file is not acceptable. Fixed with the
`cast` pattern this same file already uses in `search_suggestions` (which is
why that method has no such error) — a typed assertion in the file's own
convention, not a suppression. This touches `search`, which is outside the
reported bug; flagged to the user as the one change beyond the task's scope.

### 10. Gate results

- `task format` — 749 files already formatted
- `task lint` — all checks passed
- `task type` (pyre, CI's gate) — no type errors
- pyright (via npx; task target absent) — 0 errors, 0 warnings
- `task test` — 3848 passed, 2 skipped, 1 xfailed, 0 failures
- coverage on changed file — 73 stmts, 0 missed, 100%
- `flake8 --max-line-length=120` — zero errors
- `mypy --ignore-missing-imports` — no issues in 3 files
- `task lint-md` — 0 errors
- file lengths — 148 / 190 / 95 lines, all under the 250 cap

### 11. Runtime verification

`.env` points `MONGODB_URI` at the shared BADW cluster (`ebldev`), so it was
**not** used for verification — no test records written to a shared database.
Ran the modified service via `waitress-serve` against a local mongod
(`eblverify`), seeded with the real shapes from MNAO.11676 plus a
`"OrNS"/"59, 170"` decoy.

First run (port 8001) verified the index-slice implementation. That
implementation was then rewritten (step 8) and the casts added (step 9), so
per the re-verification hard gate that run was **void**. Re-ran against the
shipping tree (port 8002), confirming the serving process ran from
`/workspaces/ebl-api` with the current code:

| Query | Result |
| --- | --- |
| `["OrNS 59, 17"]` | `OrNS \| 59, 17` — the reported bug, fixed |
| `["OrNS 59, 17", "OrNS 59, 26ff."]` | both — MNAO.11676 link restored |
| `["*Bīt mēseri* 59, 17"]` | `*Bīt mēseri* \| 59, 17` |
| `["AfO 17,257ff."]` | `AfO \| 17,257ff.` — unspaced case unregressed |
| `["A B C D"]` | `[]` — no false positive |
| `["  Text With Space   4  "]` | `Text With Space \| 4` — normalisation kept |
| `["OrNS"]` | `[]` |
| `[]` | `[]` |

The `59, 170` decoy is correctly not matched by `["OrNS 59, 17"]`, confirming
exact matching with no prefix bleed. Server stopped and the local
`eblverify` database dropped afterwards.

Not verifiable here: the post-deploy check that
<https://www.ebl.lmu.de/library/MNAO.11676> renders its AfO entries. Requires
a deploy; left to the user.

### 12. Data hard gate

No array mixes two data types. `traditionalReferences` remains an array of
joined reference strings — one type. The endpoint contract is unchanged: a
JSON array of strings in, `AfoRegisterRecordSchema` records out. No
structured `{text, textNumber}` objects introduced, so the frontend keeps
working unchanged.

### 13. Not committed

Work finished; changes left uncommitted per the commit hard gate.
