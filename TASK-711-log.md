# TASK-711 — Work Log

## Goal
Address all findings from `TASK-711-review.md` (F1–F8) on PR #711 "Extend date metadata".

## 2026-05-07 — Implementation

### Design decisions

- **F1**: Use an iterative peel loop. On each iteration, attempt to strip a trailing marker (`!`/`?`) or a matched wrapper (`<…>`, `[…]`, `(…)`); stop when no rule fires. Single `O(n)` algorithm; no regex (regex would either need recursive patterns from the third-party `regex` module or a fixed-point loop with the same complexity). Documented in the function docstring.
- **F2**: Implement option 2 from the review — preserve the original raw input as a separate `original_value` field (`originalValue` JSON key). It is set by the parser whenever the cleaned `value` differs from the input. This guarantees that a legacy fragment loaded from MongoDB and re-saved keeps its raw representation byte-faithfully in `originalValue`. No migration script is required.
- **F3a**: `_parse_year_value` now operates on `dict(data)` (shallow copy).
- **F3b**: Added a docstring covering precedence, leniency, and the explicit-flag-override rule.
- **F4**: Each rule now strips only when the corresponding flag is `None`. If the caller set a flag (`True` or `False`), the corresponding wrapper/marker is left in `value`. Updated the test that previously locked the surprising behavior.
- **F5**: Parser defaults a missing `value` to `""` (consistent with prior behavior; required-ness is enforced at the route layer, not changed in this PR).
- **F6**: Documented intentional leniency in the docstring; no functional change (the original task instructions list non-numeric supported patterns such as `n+`, `x+n`, `n-n`, `n/n`).

### Code changes

- `ebl/fragmentarium/domain/date.py`:
  - Added `original_value: Optional[str]` to `Year`.
  - Replaced six helpers with two module-level constants (`_WRAPPERS`, `_TRAILING_MARKERS`) and one `_parse_year_value` function (iterative peel + shallow copy + flag-set guard + `original_value` capture).
  - Added `original_value = fields.String(data_key="originalValue", allow_none=True)` to `YearSchema`.

- `ebl/tests/fragmentarium/test_date.py`:
  - Replaced `test_year_schema_structured_metadata_takes_priority_over_wrapper` with two tests: one covering `True` override (no strip), one covering `False` override (no strip).
  - Added tests for mixed/nested combinations: `<5>?`, `<5>!`, `[5]?`, `[(5!)]?`, `([5?])!`, `[<(5)>]`, `<<5>>`.
  - Added tests for degenerate inputs: `<>`, `[]`, `()`, `!`, `?`, `""`.
  - Added `original_value` round-trip test via `DateSchema` (legacy DB shape).
  - Added `Month`/`Day` negative tests (extra year-only fields are silently dropped).

- `ebl/tests/factories/fragment.py`: no change needed beyond what the PR already had.

### Results

- `poetry run pytest ebl/tests/fragmentarium/test_date.py ebl/tests/fragmentarium/test_fragment_date_route.py ebl/tests/fragmentarium/test_dates_in_text_route.py --cov=ebl.fragmentarium.domain.date --cov-report=term-missing`
- See final terminal output for pass/fail and coverage numbers.
