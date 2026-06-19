# TASK-realia-reallexikon — TODO

RlA (reallexikon) entries are unique per realia entry: the live data has 0 or 1
(15,422 docs with 0, 9,750 with 1; the only doc with 3 is the throwaway "Pig"
seed). Model `reallexikon` as a single optional entry instead of a list.

## Plan

- [x] Domain: `RealiaEntry.reallexikon` → `Optional[ReallexikonEntry] = None`
- [x] Schema: replace `fields.List(...)` with a tolerant `ReallexikonField`
      (load array → first/None, also accept a single object; dump → single
      object or null). Storage stays an array; no data migration.
- [x] `_collect_reference_ids` / `_inject_entry` / `_inject_reallexikon`:
      handle the single optional entry
- [x] Factory + tests (entry, repository, route) updated for the single shape
- [x] Pre-commit gates: format, test, coverage, flake8, mypy
- [x] Verify against live data: `find`/`search` load the single entry

## Notes / flag

- API response shape for `reallexikon` changes from array to object|null.
  Acceptable on this unreleased branch, but the frontend must align.
