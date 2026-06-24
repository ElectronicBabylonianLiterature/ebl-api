# TASK-726 Work Log — RlA (reallexikon) uniqueness investigation

## 2026-06-24

- Reviewed realia domain/schema/repository on branch `add-realia`.
- Found commit `f13e6daf` collapsed `reallexikon` from a list to a single
  optional entry, premised on "live data has 0 or 1 reallexikon entries".
- Connected directly to `ebldev.realia` (24,197 docs) and inspected the
  `reallexikon` field:
  - Stored as an array on all docs.
  - 334 docs have >1 RlA entry (up to 12); genuine data (Aššur, Ehe, Gold, …).
  - `Pig` seed (the cited multi-entry example) no longer exists.
  - 9,564 distinct RlA ids, 0 duplicates globally / within-doc.
- Confirmed runtime data loss: loading `Aššur` keeps only the first RlA entry;
  the other two are silently dropped by `ReallexikonField._deserialize`
  (`value[0]`).
- Conclusion: single-entry model is invalid against live data; fix needed —
  revert `reallexikon` to a list. Documented in `TASK-726-review.md`.
- User confirmed the fix. Implemented: reverted `reallexikon` to a list.
  - `RealiaEntry.reallexikon: Sequence[ReallexikonEntry] = ()`
  - Schema field back to `fields.List(fields.Nested(ReallexikonEntrySchema))`,
    restored `tuple(...)` in post_load, removed `ReallexikonField`.
  - Restored list-based `_collect_reference_ids` / `_inject_reallexikon`;
    dropped now-unused `Optional` import.
  - Factory builds 2 RlA entries again; updated entry/repository/route tests.
  - Added regression test `test_realia_entry_schema_load_multiple_reallexikon`.
- Verified against live `ebldev`: `Aššur` now loads all 3 RlA entries
  (A. Stadt / B. Land / C. Hauptgott) instead of only the first.
- Gates: `task format` clean; realia tests 34 passed; 100% coverage on both
  changed source modules; flake8 0; mypy 0. Full `task test`: 3589 passed,
  2 skipped, 1 xfailed. `task lint-md`: 0 errors.

(Reminder: remove TASK-726-todo.md / TASK-726-log.md / TASK-726-review.md
before this PR is merged.)
