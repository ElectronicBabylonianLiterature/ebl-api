<!-- markdownlint-disable MD013 MD041 -->

# TASK-764 Handoff — PR #764 "Add the nameParts/nameBreaks migration"

| Field | Value |
| --- | --- |
| **Date** | 2026-09-16 |
| **Pull request** | [#764](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/764) |
| **Branch** | `migrate-name-breaks` → `master` |
| **Base commit** | `aaffba18` (the commit that was reviewed) |
| **Depends on** | [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) — still **open**; must merge **and deploy** before this migration is run |
| **State** | Review done, all findings addressed, gates green, committed locally as `ab66d7de` (**not pushed**), PR body updated |
| **Related files** | `TASK-764-review.md` (the review), `TASK-764-fix-log.md` (what was changed and why), `TASK-764-fix-todo.md` |

## What this PR does

A named sign used to keep its name in one array that mixed two kinds of thing: the letters of the name and the `[` `]` brackets that fall inside it. Those are now two separate arrays, `nameParts` and `nameBreaks`. This PR is the script that converts the documents already in the database.

## What was done in this round

A full review of the PR, then every finding from it was fixed.

The review found **12 issues**. Two of them had already been raised by Sourcery; the other ten were new. The most serious one was a real data-loss bug: the script read a whole document, then wrote the whole document back. Anything a user edited while the script was running got silently rolled back to the old version. That is now fixed — the script writes back only the field it changed, and only if nobody else has touched it in the meantime.

Everything the migration itself does was checked by actually running it against a throwaway database, not just by running tests.

## Findings and their status

| ID | Severity | What it was | Status |
| --- | --- | --- | --- |
| F1 | High | A whole-document write silently reverted any concurrent edit | **Fixed** — writes only the changed fields, and only to documents nobody edited since they were read; skipped documents are counted and reported |
| F2 | Medium | `--apply` could stop half-way through | **Documented** — the script is resumable by design; the docstring now says so and says what to do after an abort |
| F3 | Medium | A dry run ignored `BATCH_SIZE` and kept every pending update in memory | **Fixed** — the dry run now only counts and builds nothing |
| F4 | Medium | The error said which token was wrong but not which document | **Fixed** — the error now names the collection and the `_id` |
| F5 | Low | A `nameParts` that was not an array crashed with a bare `TypeError` | **Fixed** — raises the proper `NonAlternatingName` |
| F6 | Low | A mistyped database name produced no output and exit 0 | **Fixed** — warns per missing collection, naming the database |
| F7 | Low | The tests redefined fixtures that already exist in `conftest.py` | **Fixed** — uses the shared ones |
| F8 | Nit | An unused fixture and an unclosed client | **Fixed** |
| F9 | Nit | `Any` where the shape was known | **Fixed** — `NameToken` / `MongoDocument` aliases |
| F10 | Nit | Use `collections.abc` and PEP 585 generics like the neighbouring migrations | **Not done — see below** |
| F11 | Nit | A test name that overstated what it tested | **Fixed** |
| F12 | Nit | The docstring said `MONGODB_DB` was required but the code made it optional | **Fixed** — it is required now |

## What remains to address

### 1. F10 — pyre crashes on the modern typing style (open, low priority)

`collections.abc` imports and PEP 585 built-in generics (`list[...]`, `tuple[...]`) are what `ebl/dictionary/migrate_named_entity_tags.py` and `ebl/fragmentarium/migrate_cropped_images.py` use, so this module does not match its neighbours. It cannot, for now.

While fixing F1, `task type` started dying with `Pyre encountered an internal exception: Worker_exited_abnormally` and, on a second run, `End_of_file`. A crash, not a type error, so it named no file or line. Bisecting against a pristine tree found the trigger:

```python
UpdateOne({"_id": original["_id"], **unchanged_since_read}, {"$set": changed})
```

A `**` unpack inside that dict literal crashes pyre. Building the filter explicitly instead makes all three checkers pass, and that is what the code does now. Nothing was suppressed and no configuration was touched.

**Next step:** worth reporting upstream to pyre with a minimal reproduction. Until then, keep the `typing` spellings in this module. Anyone who "tidies" them back to `collections.abc` will get an unexplained CI crash with no error message, which is why this is written down here.

### 2. The PR body — done

The PR body was rewritten on 2026-09-16 and is now current. What changed:

- The stored-path claim is replaced by a **What it visits** section explaining that the code recurses on the `nameParts` key rather than walking a fixed path, with a table of where named signs actually occur in each of the three collections, and the evidence that `data_key="nameParts"` exists on `NamedSignSchema` only.
- The even/odd split is now justified by the grammar rules from `ebl_atf_text_line.lark`, not by "everything the parser produces today".
- New **Concurrency** and **Resumability** sections describe the F1 fix and what to do after an abort.
- The **Verification** table is refreshed for the post-fix behaviour, including the two concurrency cases and the batch-retention numbers.
- **Running it** notes that `MONGODB_DB` is now required and that a missing collection is reported by name.
- A note warns anyone tidying the typing about the pyre crash.
- The existing "Summary by Sourcery" section was preserved.

Patched with `gh api repos/... /pulls/764 -X PATCH -F body=@file`, because `gh pr edit --body` fails silently in this environment. Verified by fetching the live body back and diffing it against the draft: identical apart from a trailing newline GitHub adds.

### 3. #743 must merge and deploy first (blocking, external)

This migration writes a `nameBreaks` field. The code currently in production rejects unknown fields outright, so running this before #743 is deployed takes the site down for every fragment it touches.

**Next step:** do not run this script until #743 is merged **and deployed**. #743 is still open, and it currently carries 24 `.md` files (23 of them `TASK-74*` todo/log/handoff files) that should be removed before it merges.

### 4. The contract step is still to come (future work)

Once no legacy documents remain, the `@pre_load` adapter `separate_legacy_name_parts` in `ebl/transliteration/application/token_schemas_signs.py` can be deleted. That is a separate PR and should not be done until this migration has run against production.

### 5. Task markdown files must be removed before merge (housekeeping)

These files **are now committed** and are part of the PR: `TASK-764-todo.md`, `TASK-764-log.md`, `TASK-764-review.md`, `TASK-764-fix-todo.md`, `TASK-764-fix-log.md`, `TASK-764-handoff-todo.md`, `TASK-764-handoff-log.md`, `TASK-764-docs-todo.md`, `TASK-764-docs-log.md` and this file. They were added on request, superseding the earlier instruction that this PR add no `.md` files. **Delete all of them before the PR merges.**

## Next steps, in order

1. Push the branch — the commit is still local, so no check has run against it yet.
2. Confirm the remote checks pass on the new commit, and re-read any new Sourcery, qlty and CodeQL feedback.
3. Get the PR reviewed and approved — `mergeStateStatus` was `BLOCKED` only because of `REVIEW_REQUIRED`, never because of a failing check.
4. Merge and deploy **#743** first.
5. Delete the task markdown files.
6. Merge this PR.
7. Run the migration against production: dry run first, read the counts, then `--apply`.
8. Open the follow-up PR that deletes the `@pre_load` adapter.

## How to run it

```bash
export MONGODB_URI=...
export MONGODB_DB=...
poetry run python -m ebl.transliteration.migrate_name_breaks           # dry run, writes nothing
poetry run python -m ebl.transliteration.migrate_name_breaks --apply   # writes
```

Read the dry-run counts before using `--apply`. If a run aborts with `NonAlternatingName`, the message names the collection and the document: repair that document and run it again. Nothing already written is undone or written twice. If the run reports that documents "changed while the migration was reading them", just run it again — those are documents someone edited mid-scan, and they were deliberately left alone.

## Evidence

Gates on the committed tree: `task test-all` exit 0 — format clean, ruff clean, pyre "No type errors found", pyright 0/0/0, **4556 passed** (2 skipped, 1 xfailed), markdownlint 0 errors. Plus mypy clean, flake8 clean, migration coverage **104 statements, 0 missed, 100%**. File lengths 207 / 141 / 122 / 29, all within the 250-line limit.

Runtime verification, re-run against a throwaway database on `127.0.0.1:27017` after the final edit — never the URI in `.env`, which points at production:

```text
dry run                                fragments 2, texts 0, chapters 1; database unchanged
--apply                                24 named signs split; recombination lossless;
                                       unrelated field preserved; chapter signs migrated
second dry run                         0 / 0 / 0, idempotent
F1: edit to another field mid-scan     user's edit preserved, document still migrated
F1: edit to the migrated field         stale write refused, user's edit preserved,
                                       document left legacy, re-run migrates it
F3: batch held, 1200 docs, SIZE 500    dry run 0, apply 499
F4: non-alternating document           NonAlternatingName: fragments document 'K.7': ...
F6: database without the collections   WARNING: fragments: no such collection in database
                                       'ebl_refix_764_typo'; skipping it
```
