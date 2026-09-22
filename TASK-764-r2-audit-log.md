# TASK-764-r2-audit — Work Log

Records what was actually done, including every error and how it was recovered.

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Created this log and `TASK-764-r2-audit-todo.md` before starting.
- Honest starting position: the round-14 findings were for PR #743. **PR #764's
  own review feedback has never been fetched in this session**, so "did you
  address all the findings" cannot be answered for #764 yet. Fetching it first.

### Error made, and how it was recovered

- I created `TASK-764-fix-todo.md` and `TASK-764-fix-log.md` without first
  checking whether those names were taken. They are **tracked files on this
  branch**, part of the 14 `TASK-764-*.md` documents the branch carries, and my
  `cat >` overwrote both — 226 lines of committed content replaced by 41 of mine.
- Caught it while enumerating the branch's stray files, when the same two names
  appeared in `git diff --diff-filter=A`. `git status` confirmed them as
  modified rather than untracked.
- Recovered with `git checkout -- TASK-764-fix-todo.md TASK-764-fix-log.md`,
  which restored both from `31929977`. Nothing was lost; the content was
  committed. Re-created my own under `TASK-764-r2-audit-*` instead.
- Lesson recorded for the session: check `git ls-files` for the name before
  creating a task document on a branch that already carries some.

### Audit of every finding

**PR #764 — existing feedback fetched for the first time this session.**
1 review, 2 inline comments, 1 conversation comment, all from `sourcery-ai`.
CI at `31929977`: all green, `qlty check` *No blocking issues*, `qlty coverage
diff` 100%. Both Sourcery findings are marked *Addressed in 31929977* by the bot
itself, and I confirmed each against the current code rather than trusting the
marker.

**PR #764's own review file (`TASK-764-review.md`, F1–F12)** — checked each
against `31929977`:

| | Status verified in the tree |
| --- | --- |
| F1 whole-document `$set` | Fixed — `_update_for` sets only changed keys and filters on their pre-read values |
| F2 partial apply | Fixed by documentation plus F4; docstring states the run is resumable |
| F3 dry run retains every update | Fixed — `migrate_collection` returns `sum(1 for _ in ...)` over a generator |
| F4 guard does not name the document | Fixed — `_migrate_copy` re-raises with collection and `_id`; seen in my own rehearsal output |
| F5 non-sequence raises `TypeError` | Fixed — `_validate_is_an_array` raises `NonAlternatingName` |
| F6 mistyped `MONGODB_DB` is silent | Fixed — `migrate` warns per missing collection; seen in my rehearsal |
| F7 duplicate fixtures | Fixed — the database tests now use `conftest`'s `database` fixture |
| F8 unclosed `MongoClient` | Fixed — `database.client.close()` |
| F11 misleading test name | Fixed — now `test_a_refused_name_names_the_collection_and_the_document` |
| F12 docstring vs optional env var | Fixed — `os.environ["MONGODB_DB"]`, docstring matches |
| **F9** `Any` where the shape is known | **Justified, not changed** — see below |
| **F10** `typing` generics and `isinstance` targets | **Was still open. Fixed this round.** |

**F10, fixed.** The module used `typing.List/Dict/Tuple` and `typing.Mapping`
and `typing.Sequence` as `isinstance` targets, while the neighbouring
`ebl/dictionary/migrate_named_entity_tags.py` uses PEP 585 built-ins. Now
`from collections.abc import Iterator, Mapping, Sequence` and
`from typing import Any, Optional`, with `list[...]`, `dict[...]`, `tuple[...]`
in annotations. All three type checkers accept it.

**F9, justified rather than changed.** `separate_name_parts(name_parts: Any)`
and `migrate_document(document: Any)` take arbitrary Mongo data whose shape is
exactly what they exist to validate. Narrowing the annotation would assert the
property the function is there to check. The instruction is "avoid `Any` unless
very necessary"; validating untrusted stored data is the case where it is.

**PR #764's 14 stray `TASK-764-*.md` files — removed.** I recorded this in
`TASK-743-r15-handoff.md` and never acted on it; being on the branch, I can.
`git rm 'TASK-764-*.md'`; the staged tree now adds nothing outside `ebl/`.
Note `TASK-764-review.md` said these were "local and uncommitted" — that was
true when written and had gone stale; all 14 were committed.

**PR #743's description gave a command that does not exist.** Gate 2 said
`poetry run python task_743_migrate_name_breaks.py`. That file is gone; the
script is `python -m ebl.transliteration.migrate_name_breaks`. Anyone following
the gate would have got "No such file or directory". Corrected, along with the
two other stale references, and the dry-run result and census recorded in Gate 2.

**Round-14 findings on #743** — R14-1, R14-3, R14-5, R14-6, R14-7, R14-10 fixed
in earlier rounds; R14-2 is the frontend change and cannot be closed here;
R14-8 and R14-9 were informational with no action expected and remain recorded;
R14-4 is an open judgement call and is being put to the user.

### Re-verification after the F10 rewrite

The F10 change edited the module my clean dry run had already exercised, so that
evidence was void under the re-verify gate. Re-ran both against the final code:

- Dry run: `fragments` 38 284, `texts` 0, `chapters` 220, exit 0, no abort —
  **same counts** as the pre-F10 run.
- Census: **byte-identical** to the pre-F10 output. 5 508 869 name arrays,
  250 218 breaks, zero non-alternating.

So the numbers now recorded in PR #743's Gate 2 describe the code that will
actually ship.

### Gates on the change

- `task format` 830 files formatted · `task lint` clean · `task type` (pyre)
  **No type errors found** · pyright 0/0/0 · mypy clean · flake8 0 · lint-md 0.
- Full suite: **4556 passed, 2 skipped, 1 xfailed, 0 failed** in 532.16 s.
- `ebl/transliteration/migrate_name_breaks.py` at **100% coverage**, 208 lines.
- `qlty smells --include-tests` on the changed file: no findings.

### Not committed

Nothing was committed or pushed this round. The working tree holds the 14 staged
deletions and the F10 edit. The commit authorization given earlier was single-use
and was spent on `6e627647` on the other branch.

<!-- markdownlint-configure-file { "MD013": false } -->
