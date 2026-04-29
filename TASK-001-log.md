# TASK-001 — Work Log

## Overview
Implement `isReconstructed` and `isEmended` metadata fields on `Year`, and add parsing logic to strip
wrapper symbols (`<>`, `[]`, `()`, `!`, `?`) from raw year value strings, setting corresponding flags.

---

## Log

### 2026-04-29 — Initial exploration
- Read `TASK-001-BUG-3-api-instructions.md` for full requirements.
- Explored codebase. Key findings:
  - `Year` domain class in `ebl/fragmentarium/domain/date.py` has `value`, `is_broken`, `is_uncertain` — missing `is_reconstructed` and `is_emended`.
  - `LabeledSchema` (base for Year/Month/Day schemas) handles `isBroken`/`isUncertain`.
  - No year-value parsing logic exists; value is stored as raw string.
  - `YearFactory` uses `factory.Faker("word")` for value — needs new fields added.
  - Tests in `ebl/tests/fragmentarium/test_date.py` need extending.
- Confirmed: no MongoDB JSON Schema validation exists; only Marshmallow-based.
- Decided scope: add new fields only to `Year` (not `Month`/`Day`) to keep changes minimal.
  Add to `YearSchema` directly (not `LabeledSchema`) for the same reason.

### 2026-04-29 — Implementation
- **`ebl/fragmentarium/domain/date.py`**:
  - Added `import re`.
  - Added `is_reconstructed: Optional[bool]` and `is_emended: Optional[bool]` to `Year`.
  - Added `_parse_year_value(data: dict) -> dict` helper:
    - Strips `<n>` → sets `is_reconstructed=True`
    - Strips `[n]` → sets `is_broken=True`
    - Strips `(n)` → sets `is_uncertain=True`
    - Strips trailing `!` → sets `is_emended=True`
    - Strips trailing `?` → sets `is_uncertain=True`
    - Respects already-set flags (structured metadata wins over wrapper inference).
  - Added `is_reconstructed` / `is_emended` fields to `YearSchema`, calling `_parse_year_value`.
- **`ebl/tests/factories/fragment.py`**:
  - Added `is_reconstructed` and `is_emended` to `YearFactory`.
- **`ebl/tests/fragmentarium/test_date.py`**:
  - Added 9 new tests covering: new fields round-trip, all 5 wrapper/symbol patterns,
    clean values, structured-metadata priority, `DateKing.king` property, `DateEponymSchema`.

### 2026-04-29 — Results
- 13 unit tests in `test_date.py` → all pass.
- 22 tests total (unit + route integration) → all pass.
- Coverage on `ebl/fragmentarium/domain/date.py`: **100%** (138 stmts, 0 missed).

### 2026-04-29 — Follow-up refactor
- Reduced `_parse_year_value` complexity further by splitting parsing into small rule helpers:
  - `_apply_wrapped_value_rule`
  - `_apply_trailing_marker_rule`
  - `_set_flag_if_missing`
- Fixed robustness issue by initializing `data["value"]` before applying rules.
  This avoids potential `KeyError` when `value` is absent.
- Removed now-unused `re` import after switching from regex to string-boundary rules.
- Re-ran tests:
  - `ebl/tests/fragmentarium/test_date.py`
  - `ebl/tests/fragmentarium/test_fragment_date_route.py`
  - `ebl/tests/fragmentarium/test_dates_in_text_route.py`
  Result: 25 passed.
