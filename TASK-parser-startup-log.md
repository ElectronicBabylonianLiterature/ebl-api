# TASK-parser-startup — Work Log

## Goal

`task start` (`waitress-serve --call ebl.app:get_app`) became very slow. Audit
the cause and fix it.

## Findings

Profiled the app import:

```bash
poetry run python -X importtime -c "import ebl.app"
```

Effectively all of the cost was in building Lark parsers at module import:

- `ebl/transliteration/domain/atf_parsers/lark_parser.py` built ~11 separate
  `Lark` instances, each re-analysing the **same** `ebl_atf.lark` grammar
  (~1.7s each ≈ **19s**).
- `ebl/transliteration/domain/atf_parsers/reconstructed_text_parser.py` rebuilt
  that same grammar **again** (~2.5s).

Total ≈ 21s of redundant grammar analysis on every startup (and every test
collection / CLI invocation).

Not a realia change — it accumulated as start rules were added; each new
`Lark.open()` on the shared grammar added ~1.7s. `master` already showed the
slow behaviour, so this is a latent regression rather than something new on a
feature branch.

## Change

- Build the `ebl_atf.lark` grammar **once** as a multi-start `LINE_PARSER`
  (it was already multi-start) covering every start rule the module needs.
- Expose `WORD_PARSER`, `NOTE_LINE_PARSER`, `MARKUP_PARSER`,
  `PARALLEL_LINE_PARSER`, `TRANSLATION_LINE_PARSER`, `PARATEXT_PARSER`,
  `LABEL_PARSER` as thin `_StartParser` wrappers that pin a start rule, so the
  existing `PARSER.parse(text)` public API is unchanged.
- Point `RECONSTRUCTED_LINE_PARSER` at the shared `LINE_PARSER` (added its one
  missing start rule, `ebl_atf_text_line__break`) instead of rebuilding.
- Left `CHAPTER_PARSER`, `MANUSCRIPT_PARSER`, `LINE_NUMBER_PARSER` alone — they
  use different grammar files and build in 0.03–0.78s.

### Line-count HARD GATE (<=250 lines)

The change pushed `lark_parser.py` to 278 lines (master was already 254, over
the gate). To comply, moved the `create_transliteration_error_data`
`singledispatch` block into the existing `lark_parser_errors.py` (its natural
home — error types already live there). `lark_parser.py` re-imports it, so all
external imports keep working.

Final line counts: `lark_parser.py` 235, `lark_parser_errors.py` 50,
`reconstructed_text_parser.py` 30 — all under 250.

The disk-cache option (`Lark(cache=True)`) was rejected: it only works with
`parser="lalr"`, but this grammar is ambiguous and uses Earley.

## Result

`import ebl.app` wall time: **~22s → ~6s**. `lark_parser` import self-time
19.2s → 3.6s; `reconstructed_text_parser` 2.5s → ~0s.

## Gates

- `ruff format --check` — pass
- `ruff check ebl` — pass
- `pyre check` — no type errors
- Tests: `ebl/tests/transliteration/` + `ebl/tests/corpus/test_parse_chapter.py`
  — 1696 passed, 1 skipped, 1 xfailed
- `task lint-md` — pass (new task `.md` files)

## Coverage (affected modules)

Broad parse-path suite (`transliteration/`, `corpus/`, `fragmentarium/`,
`signs/`, `atf_importer/` — 3017 passed):

| Module | Cover | Missing |
| --- | --- | --- |
| `lark_parser.py` | 99% | 185 (`validate_line` Tree guard) |
| `reconstructed_text_parser.py` | 100% | — |
| `lark_parser_errors.py` | 100% | — |

`lark_parser.py:185` is the unchanged `validate_line` Tree-guard, uncovered on
`master` too (coverage-neutral).

The error-dispatch branches in `lark_parser_errors.py` were a **pre-existing**
gap (the unregistered-error fallthrough, the `UnexpectedInput` formatting branch,
and the `VisitError` re-raise were uncovered on `master`, where this code lived
in `lark_parser.py`). Added `ebl/tests/transliteration/test_lark_parser_errors.py`
to close it — the module is now 100% covered.
