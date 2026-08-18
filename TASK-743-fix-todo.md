# TASK-743-fix TODO — Address the findings of the PR #743 review

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743>
Branch: `fix-type-checker-blind-spots` -> `master`
Source of findings: `TASK-743-review.md`

## Setup

- [x] Re-read `.github/instructions/copilot.instructions.md`
- [x] Create `TASK-743-fix-todo.md`
- [x] Create `TASK-743-fix-log.md`

## F1 — duplicate `__all__` in `chapter_schemas.py`

- [x] Delete the second `__all__` block; keep the complete first one

## F2 — `TextLine.merge` cast unsound for subclasses (Sourcery)

- [x] Mark `TextLine` `@final` so the cast is provable, not merely true today
- [x] Confirm all three type checkers still pass

## F3 — three CodeQL alerts

- [x] `signs_transformer.py` — `scan_values(lambda value: bool(value))` -> `scan_values(bool)`
- [x] `token_base.py` — `SignsCollectingVisitor.reset` / `.result_string`
      `...` -> `raise NotImplementedError`, matching `Token.value` / `Token.parts`

## F4 — six qlty blocking issues

- [x] `retrieve_annotations_helpers.py` `match` — 7 returns -> mapping lookup
- [x] `named_signs.py` `Logogram.of` — 6 parameters
- [x] `named_signs.py` `Logogram.of_name` — 6 parameters
- [x] `test_named_sign_logogram.py` `test_logogram` — 9 parameters
- [x] `test_named_sign_number.py` `test_number` — 7 parameters
- [x] `test_named_sign_reading.py` `test_reading` — 8 parameters
- [ ] Also: similar-code pair in the two new test factories — **DECLINED**
      with a rationale; not in the current blocking six
- [x] Also: `type` builtin shadowing in `match`

## F5 — stale PR description

- [x] Draft the corrected description text
- [x] ASKED the user; they chose "patch it now"; patched and verified

## F6 — `NamePart` delegates only 3 of ~13 `Token` members

- [x] Stop `NamePart` being a `Token`, or delegate the rest
- [x] Confirm the `nameParts` wire format is still byte-identical to master

## F7 — five pre-existing mypy errors in `ebl/atf_importer/**`

- [ ] `legacy_atf_transformers.py` `Pattern.search` arg type — **NOT DONE**,
      deliberately: see the log and the review `Resolution` section
- [x] `logger.py` `Path()` arg type
- [x] `lemmatization.py` two TypedDict right-hand-side values
- [x] `atf_indexing_visitor.py` assignment to a `None`-typed target
- [x] Confirm touching these files does not break pyright / pyre / the 250-line
      limit

## Verify

- [x] `task format`
- [x] `task lint`
- [x] `task type` (pyre — CI gate)
- [x] `task type-pyright`
- [x] `task test`
- [x] Coverage 100% on every line added, modified or moved
- [x] `poetry run flake8 <changed> --max-line-length=120`
- [x] `poetry run mypy <changed> --ignore-missing-imports`
- [x] `task lint-md`
- [x] 250-line limit on every touched `*.py`
- [x] Run the modified service and exercise the affected routes (re-run after
      every rewrite — earlier evidence is void)
- [x] Re-diff `nameParts` wire output against master

## Close out

- [x] Update `TASK-743-review.md` with the resolution of each finding
- [x] Re-read the copilot instructions; confirm every gate honoured
- [x] Report gates run and their results
- [x] Do NOT commit or push

## Outcome

- F1, F2, F3, F4, F5, F6 — fixed.
- F7 — 4 of 5 mypy errors fixed; `legacy_atf_transformers.py` left, with reason.
- Extra work the fixes forced: `test_parse_word.py` split (875 -> 66 lines plus
  six case modules) to keep the 250-line gate.
- All gates green. Nothing committed, nothing pushed.
