# TASK-parser-review — TODO

Address code review findings on the optimised Lark parser startup
(`lark_parser.py`).

## Findings to address

- [x] Overall #1: `_StartParser` only exposed `parse`; other `Lark` methods
      (`parse_interactive`, `lex`, `options`) would fail. Delegate unknown
      attributes via `__getattr__`.
- [x] Overall #2: Remove the temporary `TASK-parser-startup-*.md`
      worklog/TODO artifacts noted for deletion before merge.
- [x] Comment #1: Deduplicate `ATF_GRAMMAR_STARTS` (wrap in `pydash.uniq`) so
      overlaps with `LINE_PARSER_STARTS` cannot hide mistakes.

## Own review findings

- [x] Self-review #1: Fix `__getattr__` infinite recursion on copy/pickle
      (read `_parser` from `__dict__`, raise `AttributeError` when absent).
- [x] Export detailed review to `TASK-parser-review-review.md`
      (Summary / Findings / Severity / Reproduction Steps / Recommendation).

## Gates / cleanup

- [x] Add type hints to `_StartParser.parse` (`text: str`, `-> Tree`).
- [x] HARD GATE: keep every changed `*.py` <= 250 lines
      (`lark_parser.py` = 240).
- [x] HARD GATE: 100% coverage on touched lines
      (`test_start_parser.py` covers default start, `__getattr__` delegation,
      and missing-attribute path).
- [x] `task format` (ruff format --check)
- [x] `task lint` (ruff check)
- [x] `task type` (pyre — no type errors)
- [x] Tests: transliteration + corpus parser suites pass
- [x] `task lint-md` (markdown gate for these docs)
- [ ] Reminder: remove `TASK-parser-review-*.md` (todo/log/review) before the
      PR is merged
