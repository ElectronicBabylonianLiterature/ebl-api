<!-- markdownlint-disable MD013 -->

# TASK-748 — Work log

## 2026-09-15

### Start

- Created this log and `TASK-748-todo.md` before starting. TASK-747's files do
  not carry forward.
- Trigger: "Address the remaining issues."
- Starting point: `fix-type-checker-blind-spots` at `38b042a6`, clean, pushed.
  PR #743 and the new PR #764 both open.

### Entries

#### PR #743 feedback sweep

Fetched submitted reviews, inline diff comments, issue comments and the GraphQL
review threads with their resolved state. **41 threads, 3 unresolved.**

Human review: `Fabdulla1` requested changes on 2026-08-07 and **approved** on
2026-09-01 ("just small changes that need to be done and then it should be good
to merge"). All of their threads are resolved.

The three unresolved:

**1. `sourcery-ai`, `ebl/transliteration/domain/text_line.py:150`, bug_risk —
ADDRESSED, and in fact fixed by this PR.**

> The new `merge` return type and cast can be unsound for subclasses of
> `TextLine`. [...] If `L` is a subclass of `TextLine`, callers will receive a
> `TextLine` instance while the type system says it is `L`.

`merge` does `return cast(L, TextLine.of_iterable(...))`, so the concern is real
in principle. It cannot occur here:

- `TextLine` is declared **`@final`** — and `git diff` against the merge base
  shows **this PR added it**, both the `final` import and the decorator. So the
  subclass the finding depends on cannot be written; the type checkers reject it.
- Confirmed no subclass of `TextLine` exists anywhere in the tree.
- The `-> L` signature and the `cast` both **predate this PR** — they are already
  present at the merge base. What this branch changed is to close the hole.

The thread is marked **outdated** by GitHub, consistent with the code having
moved since 2026-07-23.

**2. `qltysh`, `ebl/tests/factories/fragment.py:66` — justified (duplication B).**
**3. `qltysh`, `ebl/transliteration/domain/tokens.py:31` — justified (duplication A).**

These are the two qlty blocking issues still reported. Both are lists that share
a shape and nothing else: an `__all__` re-export list against another `__all__`,
and an `__all__` against `PREFIXES`, a list of museum-number prefixes.

**Problem spotted while checking them:** that justification lived only in
`TASK-746-log.md` and `TASK-745-handoff.md`, **both of which gate 3 deletes
before merge**. After the merge nothing would record why two qlty findings were
accepted, and the next person to run qlty would re-investigate from scratch.
Moved into the PR description, which survives.

#### Proof that the documented qlty command was vacuous

The instructions prescribed `qlty smells <changed files>`. Run that way on two
test files:

```text
[1/3] Checking structure of 0 files...     0.00s
[2/3] Looking for duplication across 0 files...  0.00s
```

**Zero files.** It analysed nothing and exited clean. With `--include-tests` the
same command checks 2 files. So the gate as written could never have caught any
of the four duplications on this PR — all of which are in `ebl/tests/`.

Updated `.github/instructions/copilot.instructions.md` accordingly (that file is
already part of this PR, which is what added the qlty hard gate):

- gate 9 in the pre-commit list is now
  `qlty smells --include-tests <changed files>`, flagged as not optional
- added that `--include-tests` is mandatory and why: qlty Cloud does not exclude
  tests, so omitting it runs a weaker check than the one gating the build
- added how to enumerate what a branch introduces —
  `qlty smells --all --include-tests` at `HEAD` versus a detached worktree at
  `origin/master`, then diff — because a changed-files run cannot see a
  duplication shared with an untouched file
- added that **qlty Cloud counts one issue per file involved**, not per
  duplication, so a count must be reconciled on that basis before being called
  stale
- noted that `qlty init --yes --skip-plugins` installs no plugins, so a local
  `qlty check` under that setup reports nothing and proves nothing

#### Durable justification

Added a **Review findings** section to `TASK-743-fix-pr-body.md` recording the
two accepted qlty findings with their reasoning, the two that were fixed and
how, the `--include-tests` trap, and the Sourcery resolution. The PR description
survives the gate 3 cleanup; the task files do not.

#### Gates

Only markdown changed — `git status` shows no `.py` files — so the code is
covered exactly by the existing runs. Ran the full list anyway:

| Gate | Result |
| --- | --- |
| `task format` | 886 files already formatted |
| `task lint` | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings |
| `task test` | **4530 passed, 2 skipped, 1 xfailed** |
| `task lint-md` | 0 errors |

Gates 6-9 (per-module coverage, flake8, mypy, `qlty smells`) have no changed
Python to run against.

**Correction.** I predicted this run would come back 4548. It is 4530, and 4530
is right: 4548 was the count at `0919dee6`, *before* the migration files left
the branch, and removing them took 18 migration tests with it. I quoted the
pre-removal number by mistake; the post-removal baseline established on the
reduced branch was already 4530.

#### PR description applied

User asked for it. Fetched the live body first (544 lines) and diffed it against
the file before overwriting: the change is **purely additive**, 33 lines
appended, nothing else touched.

Applied with `gh api repos/.../pulls/743 -X PATCH -F body=@TASK-743-fix-pr-body.md`
— not `gh pr edit --body`, which fails silently in this repo. Re-fetched and
diffed afterwards: identical apart from the trailing newline the API adds.
**Verified.** The Review findings section is live at line 545 of the
description, so the reasoning for the two accepted qlty findings now survives
the gate 3 cleanup that deletes the task files.

#### Commit

`5c94f201` — committed and pushed; local and remote verified identical, working
tree clean.
