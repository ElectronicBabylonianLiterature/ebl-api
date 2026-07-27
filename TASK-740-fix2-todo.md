# TASK-740-fix2 — TODO

Address every finding raised in `TASK-740-review2.md` for PR #740.

This is a new task and gets its own TODO / log files; the review task's files
do not carry forward.

## Blockers

- [x] F1. Fix the pyre error: `AbstractWordSchema.word_class` declared
      `ClassVar[Type[Word]]` but never initialized
      (`token_schemas_words.py:53`). Verify with `task type`.
- [x] F2. Fix `task type-pyright` — 41 errors on two changed files
  - [x] F2a. `ebl/tests/factories/archaeology.py` (40 errors)
  - [x] F2b. `ebl/tests/fragmentarium/test_fragment_repository_updates.py:102`
        (`tuple[Literal['aklu I']]` where `Sequence[WordId]` is expected)

## Other findings

- [x] F3. Correct the PR description — it claims no `try`/`except` was added,
      but `_find_by_realia_ids` swallows `PyMongoError`. **Outward-facing:
      prepare the text, confirm with the user before PATCHing GitHub.**
- [x] F4. Clear the 5 mypy errors in touched files
  - [x] F4a. `fragment_metadata.py:9` — `lark_parser` `PARSE_ERRORS`
  - [x] F4b. `fragment_metadata.py:9` — `lark_parser` `parse_markup_paragraphs`
  - [x] F4c. `text_line.py:120` — unexpected kwarg `unique_lemma` for `evolve`
  - [x] F4d. `text_line.py:144` — `merge` return type vs supertype
  - [x] F4e. `word_tokens.py:106` — incompatible return value type
- [x] F5. Document the deliberate degrade-on-read / fail-hard-on-validate
      asymmetry. Code comments are forbidden by the instructions, so this goes
      in the PR description.
- [x] F6. `ocredSigns` mapping: add a test in
      `test_fragment_repository_updates.py`, or drop the hunk.
- [x] F7. qlty findings
  - [x] F7a. Collapse the duplicated `make_token` bodies (similar-code x2)
  - [x] F7b. Acknowledge the 10 function-parameters comments (test fixtures)
- [x] F8. Transliteration-update annotation behaviour — needs the user's
      product decision; surface it, do not silently decide.
- [x] F9. Remove the nine committed `TASK-740-*.md` tracking files.

## Gates before reporting complete

- [x] G1. `task format`
- [x] G2. `task lint`
- [x] G3. `task type` (pyre — the gate CI enforces; find a way to run it)
- [x] G4. `task type-pyright`
- [x] G5. `task test` — full suite, 0 failures
- [x] G6. 100% coverage on every changed module
- [x] G7. `poetry run flake8 <changed> --max-line-length=120`
- [~] G8. mypy — 1 remaining error, deferred to #743 (see F4b)
- [x] G9. `task lint-md`
- [x] G10. 250-line limit on every changed `*.py`
- [x] G11. Runtime verification of the affected routes against the rewritten
      code (the previous run is void once the code changes)
- [x] G12. Re-read the instructions; report gates and results; commit nothing
