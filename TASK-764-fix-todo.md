# TASK-764-fix TODO — Address every finding from the PR #764 review

Source of findings: `TASK-764-review.md` (F1–F12).
Branch `migrate-name-breaks`, base commit `aaffba18`.

Status legend: `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked.

## 0. Setup (hard gate: before any work)

- [x] Create `TASK-764-fix-todo.md`
- [x] Create `TASK-764-fix-log.md`
- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting
      complete

## 1. Source changes — `ebl/transliteration/migrate_name_breaks.py`

- [x] **F1 (High)** Narrow the write to the top-level keys that actually
      changed, and add the pre-migration value as an update predicate so a
      concurrently edited document is skipped instead of overwritten
- [x] **F1** Report the shortfall: compare `matched_count` against the number
      of updates attempted and warn with a re-run instruction
- [x] **F2** Document in the module docstring that `--apply` is resumable and
      that the response to an abort is to fix the document and re-run
- [x] **F3 (Medium)** Stop building `batch` at all during a dry run so
      `BATCH_SIZE` is honoured in both modes
- [x] **F4 (Medium)** Re-raise `NonAlternatingName` with the collection name
      and the document `_id`
- [x] **F5 (Low)** A `nameParts` that is not a sequence must raise
      `NonAlternatingName`, not a bare `TypeError`
- [x] **F6 (Low)** Warn per missing collection so a mistyped `MONGODB_DB`
      cannot look like success
- [x] **F9 (Nit)** Replace `Any` where the shape is known to be
      `Mapping[str, Any]`
- [~] **F10 (Nit)** Use `collections.abc` for `isinstance` targets and PEP 585
      built-in generics, matching the neighbouring migrations
- [x] **F12 (Nit)** Make `MONGODB_DB` match the documented contract

## 2. Test changes — `ebl/tests/transliteration/test_migrate_name_breaks.py`

- [x] **F7 (Low)** Delete the duplicated `mongo_client` / `database` fixtures
      and use the ones in `ebl/tests/conftest.py`
- [x] **F8 (Nit)** Drop the unused `database` parameter and close the client
- [x] **F11 (Nit)** Rename `test_a_refused_name_stops_the_document`
- [x] New test: a document edited mid-run is skipped, not overwritten
- [x] New test: the skip is reported to the operator
- [x] New test: the guard names the collection and the document
- [x] New test: a non-sequence `nameParts` raises `NonAlternatingName`
- [x] New test: a missing collection is warned about
- [x] New test: unrelated top-level fields are not rewritten
- [x] New test: `MONGODB_DB` contract

## 3. Gates (all must pass; none may be skipped)

- [x] HARD GATE: no `*.py` file over 250 lines (split files if needed)
- [x] HARD GATE: mixed-type arrays — introduce none
- [x] `task format`
- [x] `task lint` (ruff)
- [x] `task type` (pyre — the gate CI enforces)
- [x] `task type-pyright`
- [x] `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] `poetry run flake8 <changed modules> --max-line-length=120`
- [x] `poetry run pytest <changed modules> --cov=... --cov-report=term-missing`
      — 100% on every changed file
- [x] `task test` — full suite, 0 failures
- [x] `task lint-md`

## 4. Re-verification (hard gate: re-verify after every rewrite)

- [x] The earlier review's runtime run is VOID — the implementation changed.
      Re-run the migration end to end against a LOCAL throwaway mongo
      (127.0.0.1:27017, never `.env`)
- [x] Re-confirm: dry run writes nothing, `--apply` splits correctly,
      recombination is lossless, second run reports 0
- [x] Re-confirm F1 is fixed: the concurrent-edit reproduction must now
      preserve the user's edit
- [x] Re-confirm F3 is fixed: measure the `batch` local in both modes
- [x] Re-confirm F4 is fixed: the guard names the document
- [x] Drop every throwaway database afterwards

## 5. Close out

- [x] Update `TASK-764-review.md` so the findings reflect their resolution
- [x] Report which gates ran and their results
- [ ] Do NOT commit or push — no approval has been given for this task
- [ ] Remind to remove all `TASK-764*.md` files before the PR merges

## Notes on partly-done items

- **F10** is marked `[~]`, not `[x]`. `collections.abc` imports and PEP 585
  built-in generics were written, then reverted: pyre crashes on this module
  with them in place. The `typing` spellings are the only ones that pass all
  three checkers, so the neighbouring migrations' style could not be matched
  here. This is recorded in `TASK-764-review.md` and in the fix log. Nothing was
  suppressed and no configuration was changed.
