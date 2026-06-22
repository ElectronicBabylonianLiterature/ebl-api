# TASK-parser-review — Work Log

Branch: `optimize-lark-parser-startup`

## Context

A prior change consolidated the per-start `ebl_atf.lark` parsers into one
multi-start `LINE_PARSER` with thin `_StartParser` wrappers. A code review
raised three findings to address before merge.

## Actions

1. **`_StartParser` attribute delegation**
   - File: `ebl/transliteration/domain/atf_parsers/lark_parser.py`
   - Added `__getattr__` delegating unknown attributes to the wrapped `Lark`
     instance, so `parse_interactive`, `lex`, `options`, etc. keep working on
     `WORD_PARSER`/`NOTE_LINE_PARSER`/… wrappers.
   - Added type hints to `parse` (`text: str`, `**kwargs: object`, `-> Tree`).

2. **Deduplicate `ATF_GRAMMAR_STARTS`**
   - Wrapped the combined start-symbol list in `pydash.uniq([...])` (pydash was
     already imported) so any overlap with `LINE_PARSER_STARTS` is removed
     while order is preserved.

3. **Remove temporary artifacts**
   - Deleted `TASK-parser-startup-log.md` and `TASK-parser-startup-todo.md`
     (their only open item was the "remove before merge" reminder).

4. **Own review — `__getattr__` recursion fix**
   - Reviewing the change locally (`copy.deepcopy(WORD_PARSER)`) surfaced a
     `RecursionError`: the naive `getattr(self._parser, name)` re-enters
     `__getattr__` when `_parser` is absent during copy/pickle reconstruction.
   - Fixed by reading `_parser` from `self.__dict__` and raising
     `AttributeError` on `KeyError`. Verified `copy`/`deepcopy` now succeed.
   - Detailed review exported to `TASK-parser-review-review.md`.

5. **Tests / coverage**
   - Added `ebl/tests/transliteration/test_start_parser.py` covering:
     default-`start` parse path, `__getattr__` delegation (`options`), the
     missing-attribute `AttributeError` path, the uninitialised-`_parser`
     branch, and wrapper copyability.
   - Adjusted the missing-attribute assertion to use a variable attribute name
     to satisfy ruff `B018`/`B009`.

## Verification

- `ruff format --check`: passed.
- `ruff check`: all checks passed.
- `pyre check`: no type errors.
- Tests: `test_start_parser.py`, `test_atf_parser.py`,
  `test_reconstructed_text_parser.py`, and `ebl/tests/corpus/` — all passed.
- Coverage: every touched line in `lark_parser.py` covered. Remaining misses
  (parse_reading/erasure/line, split_paragraphs, parse_parallel_line,
  clean_line) are pre-existing and covered by other test modules; none were
  modified by this task.
- `lark_parser.py` is 240 lines (under the 250-line hard gate).

## Outstanding

- Remove `TASK-parser-review-*.md` before the PR is merged.
