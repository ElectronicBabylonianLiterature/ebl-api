# TASK-740 Split — Work Log

## Task

Split the working tree: everything not directly related to the realia
annotation API moves to a new branch off `master` with its own PR. The
user authorised the branch, commits, push and PR creation in that
message.

## Log

### Step 1 — Tracking files

Created `TASK-740-split-todo.md` and `TASK-740-split-log.md` before any
git operation.

### Step 2 — Snapshot and classify

Snapshotted the whole working tree twice before touching git: a full
`git diff HEAD --binary` patch and a copy of all 28 changed files.

Classified hunk by hunk. Two files needed splitting across both groups:

- `ebl/tests/factories/archaeology.py` — the `EX` excavation prefix is
  the CI fix (realia); the factory import rewrite is pyright (split).
- `ebl/tests/fragmentarium/test_fragment_repository_updates.py` — the
  `update_field` guard test is the realia coverage note; the `WordId`
  hunk is pyright (split).

### Step 3 — Building the split branch

Created worktree on `fix-type-checker-blind-spots` off `origin/master`.
Ten Group B files were byte-identical between `master` and the PR head,
so they were copied wholesale. Five differed because #740 already edits
them, so their hunks were re-applied by hand against `master`'s version.

### Step 4 — Two things had to move back to #740

**`ebl/fragmentarium/domain/fragment.py`.** On `master` this file is 291
lines — already over the 250-line limit, and #740 is precisely the change
that brings it under by extracting `fragment_metadata.py`. Putting my
`set_scopes` and E203 hunks in a parallel PR would mean either shipping a
file over the limit or duplicating #740's whole restructure. Left the
file out of the split branch.

**The `Scope` typing chain.** `fragments.py` (route) ->
`fragment_updater.update_scopes` -> `fragment.set_scopes` must agree on
`Sequence[Scope]`. With `fragment.py` pinned to #740, splitting the chain
across two branches would leave the types inconsistent on both. So
`scopes.py`, `fragment_updater.py` and `fragments.py` stay with #740 too.

Mistake made and recovered: the first attempt at this move ran
`cd $WORKTREE && git checkout ...` followed by a `cp` loop that still had
the worktree as its cwd, so the three files were copied back into the
worktree instead of the main tree. Caught it on the next `git status` and
redid the move with absolute paths for both sides.

### Step 5 — Consequence for #740

With the type-checker work removed, `mypy` on the realia branch reports
its original 10 errors again — review finding 4 is reopened there. Six
are the `lark_parser` shadowing and three are the `text_line` /
`word_tokens` casts, all fixed by the split branch; they clear once it
merges. Reported to the user rather than papered over.

### Step 6 — Gates on the split branch

| Gate | Result |
| --- | --- |
| `task format` | clean |
| `task lint` (ruff) | All checks passed |
| `mypy --ignore-missing-imports` | 0 errors on changed files |
| pyright | 9 errors, all factory_boy stub bugs |
| `flake8 --max-line-length=120` | 0 errors |
| 250-line limit | all changed files within limit |
| `task test` | see below |

Two extra mypy errors appeared on the split branch that do not exist on
the realia branch, because #740 fixes them incidentally: the
`NamedEntity` generator converter on `Fragment.named_entities` and the
`TokenIndex` index in `TextLine.update_lemma_annotation`. Fixed both on
the split branch so its own touched files are clean; they will conflict
trivially with #740 and resolve to the same code.

### Step 7 — Result

Split branch pushed as `fix-type-checker-blind-spots`, commit `e3150b3d`,
28 files, +142/-89. Opened as PR #743.

Realia branch working tree re-verified after the split: `task format`
clean, `task lint` passed, `task lint-md` 0 errors, `task test` 3938
passed / 2 skipped / 1 xfailed. It remains **uncommitted** — the user
authorised commits for the split-out work only.
