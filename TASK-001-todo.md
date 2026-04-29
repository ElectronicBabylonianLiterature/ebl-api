# TASK-001 — TODO List

## Status Legend
- [ ] Not started
- [x] Completed
- [~] In progress

---

## Tasks

- [x] Explore existing date model/DTO structure
- [x] Create task documentation files (todo + log)
- [x] Add `is_reconstructed` and `is_emended` to `Year` domain class (`ebl/fragmentarium/domain/date.py`)
- [x] Add `is_reconstructed` and `is_emended` fields to `YearSchema` (serialization/deserialization)
- [x] Implement `_parse_year_value` helper and integrate into `YearSchema.make_year`
- [x] Update `YearFactory` in `ebl/tests/factories/fragment.py`
- [x] Update/extend tests in `ebl/tests/fragmentarium/test_date.py`
  - [x] Test new `isReconstructed` / `isEmended` fields round-trip
  - [x] Test parsing: `<n>` → reconstructed, `n!` → emended, `[n]` → broken, `(n)` / `n?` → uncertain
  - [x] Test backward compatibility (clean values pass through unchanged)
  - [x] Test `DateKing.king` property (found + not found)
  - [x] Test `DateEponymSchema` round-trip
- [x] Run full test suite — 13 unit tests passed, 100% coverage on `date.py`
  All 22 tests (unit + route integration) pass.
