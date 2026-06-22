# TASK-parser-startup — TODO

Audit and fix slow `task start` (waitress app startup).

## Investigation

- [x] Reproduce slow startup and profile `import ebl.app` with `python -X importtime`
- [x] Identify dominant cost
- [x] Confirm whether it is a regression (compare against master / git history)

## Implementation

- [x] Consolidate the per-start `ebl_atf.lark` Lark parsers into a single
      multi-start parser with thin `_StartParser` wrappers (preserve public API)
- [x] Reuse the shared parser in `reconstructed_text_parser` instead of
      rebuilding the grammar
- [x] Keep `CHAPTER_PARSER`, `MANUSCRIPT_PARSER`, `LINE_NUMBER_PARSER` separate
      (different grammar files, cheap to build)

## Gates / cleanup

- [x] HARD GATE: keep every changed `*.py` <= 250 lines
      (extract error dispatch into `lark_parser_errors.py`)
- [x] `task format` (ruff format --check)
- [x] `task lint` (ruff check)
- [x] `task type` (pyre)
- [x] Tests: transliteration + corpus parser suites
- [x] Coverage on affected modules: `lark_parser_errors.py` now 100%
      (added `test_lark_parser_errors.py` to close the pre-existing gap)
- [x] `task lint-md` (markdown gate for these docs)
- [ ] Reminder: remove `TASK-parser-startup-*.md` before the PR is merged
