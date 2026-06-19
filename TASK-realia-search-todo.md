# TASK-realia-search — TODO

Fix `GET /realia` search crash: `RealiaEntrySchema` does not match the real
`realia` collection data shape.

## Root causes

- [x] **type**: stored as free-text strings (`"Personal names"`, etc.), not
  `RealiaType` enum names → `NameEnumField(RealiaType)` → "Invalid value."
- [x] **reallexikon[].reference**: stored as a bibliography-id string
  (`"rla_1_2b"`), not a nested reference object → `fields.Nested` →
  "Invalid input type."

## Plan

- [x] Change `RealiaEntry.type` to `Sequence[str]`; drop unused `RealiaType` enum
- [x] `RealiaEntrySchema.type` → `fields.List(fields.String())`
- [x] Add tolerant reference field for `reallexikon[].reference`
      (load string id → `Reference`; load/serialize full object for the API)
- [x] Confirm `_inject_reallexikon` still attaches bibliography document
- [x] Update factory + tests (`test_realia_entry`)
- [x] Add test for production-shape load (string reference, free-text type)
- [x] Pre-commit gates: format, test, coverage, flake8, mypy (changed files clean;
      pre-existing unrelated `scopes.py` mypy errors flagged, left untouched)

## Out of scope (flag only)

- Dropped-on-load fields in real data: `lemma`, `realiaId`, `crossReferences`,
  `afoCrossReferences`, `afoRegister[].id` (no crash; feature decision).
