# TASK-parser-review — Review

Detailed review of the changes on branch `optimize-lark-parser-startup`
(file `ebl/transliteration/domain/atf_parsers/lark_parser.py` and the new
`ebl/tests/transliteration/test_start_parser.py`).

## Summary

The branch consolidates the per-start ATF Lark parsers into one multi-start
`LINE_PARSER` fronted by thin `_StartParser` wrappers, plus the three review
fixes (attribute delegation, `pydash.uniq` dedup of `ATF_GRAMMAR_STARTS`, type
hints). The functional behaviour of all public `parse_*` helpers is preserved
and verified locally. One latent regression was found in the first delegation
implementation and fixed during this review.

## Findings

1. **`__getattr__` infinite recursion when the wrapper is copied/pickled.**
   The initial fix used `return getattr(self._parser, name)`. When `_parser`
   is not yet present in `__dict__` (e.g. during `copy`/`deepcopy`/`pickle`
   reconstruction, which builds the instance without calling `__init__`),
   accessing `self._parser` re-enters `__getattr__`, recursing forever. The
   original code used real `Lark` objects, which are copyable, so this was a
   behavioural regression introduced by the wrapper.
   - Resolution: read `_parser` from `self.__dict__` and translate a missing
     key into `AttributeError`, so copy/pickle machinery can fall back
     correctly. Verified `copy.copy`/`copy.deepcopy` now succeed and the
     copied wrapper still parses.

2. **Duplicate start symbols in `ATF_GRAMMAR_STARTS` (from existing review).**
   Addressed by wrapping the combined list in `pydash.uniq([...])`, preserving
   order while removing any overlap with `LINE_PARSER_STARTS`.

3. **`_StartParser` only exposed `parse` (from existing review).**
   Addressed via the recursion-safe `__getattr__` delegation above; other
   `Lark` members (`options`, `parse_interactive`, `lex`, …) now work on the
   wrappers.

No correctness, security, or regression issues remain outstanding. The diff
adds no I/O, no untrusted input handling, and no new dependencies (`pydash`
was already imported).

## Severity

| Finding | Severity | Status |
| --- | --- | --- |
| 1. `__getattr__` recursion on copy | Medium (latent regression) | Fixed |
| 2. Duplicate start symbols | Low (maintainability) | Fixed |
| 3. Limited wrapper API surface | Low (forward-compat) | Fixed |

## Reproduction Steps

Finding 1 (before the fix):

```python
import copy
from ebl.transliteration.domain.atf_parsers.lark_parser import WORD_PARSER
copy.deepcopy(WORD_PARSER)  # -> RecursionError
```

After the fix:

```python
import copy
from ebl.transliteration.domain.atf_parsers.lark_parser import WORD_PARSER
copy.deepcopy(WORD_PARSER).parse("kur")  # -> Tree, no error
```

## Recommendation

Merge after the temporary `TASK-parser-review-*.md` artifacts are removed.

Verification performed locally:

- `ruff format --check`: passed.
- `ruff check`: all checks passed.
- `pyre check`: no type errors.
- Tests: `test_start_parser.py`, `test_atf_parser.py`,
  `test_reconstructed_text_parser.py`, `test_parse_erasure.py`,
  `test_parse_parallel_line.py`, and `ebl/tests/corpus/` — 548 passed.
- Behaviour: parsers build at import, wrappers delegate, all touched lines in
  `lark_parser.py` are covered, and the wrapper is now copyable.
- `lark_parser.py` is 244 lines (under the 250-line hard gate).
