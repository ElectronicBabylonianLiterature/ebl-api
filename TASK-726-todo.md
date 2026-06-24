# TASK-726 — RlA (reallexikon) entries no longer unique per realia

## TODO

- [x] Locate realia/reallexikon domain, schema, and repository code
- [x] Connect to the live `ebldev` database and inspect realia data directly
- [x] Quantify how many realia docs hold >1 RlA entry
- [x] Confirm whether multi-entry docs are real data or seed leftovers
- [x] Check for duplicate RlA ids (within-doc and cross-doc)
- [x] Confirm runtime impact of the single-entry model on real data
- [x] Write up findings in `TASK-726-review.md`
- [x] Decide with user whether to apply the fix (revert reallexikon to a list)
- [x] Implement fix and update factory/tests; add multi-entry regression test
- [x] Run gates: format, realia tests, 100% coverage, flake8, mypy
- [x] Full `task test` suite passes (3589 passed, 2 skipped, 1 xfailed)
- [ ] Remind to remove TASK-726-*.md before PR merge
