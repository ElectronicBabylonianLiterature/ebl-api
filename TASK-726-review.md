# TASK-726 Review — RlA (reallexikon) entries are not unique per realia

## Summary

The branch `add-realia` models `RealiaEntry.reallexikon` as a single optional
entry (commit `f13e6daf`, "Model realia reallexikon as a single optional
entry"). That change was justified by the assumption that "the live data has 0
or 1 reallexikon entries (only the throwaway 'Pig' seed has more)".

Direct inspection of the live `ebldev` realia collection shows this assumption
is false. **334 realia documents legitimately contain more than one RlA
entry.** The current single-entry deserializer keeps only `value[0]` and
silently drops the rest, causing data loss in every `find`/`search` API
response for those entries.

## Findings

Data inspected directly against `ebldev.realia` (24,197 documents):

- `reallexikon` is stored as an array on every document.
- Distribution of RlA entries per document:
  - 0 entries: 15,130
  - 1 entry: 8,733
  - 2 entries: 243
  - 3 entries: 53
  - 4 entries: 24
  - 5 entries: 7
  - 6 entries: 3
  - 8 entries: 2
  - 9 entries: 1
  - 12 entries: 1
- **334 documents have >1 RlA entry.**
- The multi-entry documents are genuine scholarly data, not seed leftovers.
  Examples: `Aššur` (A. Stadt / B. Land / C. Hauptgott), `Ehe` (A.–B. / C. / D.
  / E.), `Gold`, `Gott`, `Haus`, `Handel`, `Gesellschaft`, `Girsu`, …
- The `Pig` seed cited as the only multi-entry case **no longer exists** in
  `ebldev`.
- RlA `id` values are unique: 9,564 distinct ids, 0 duplicates globally, and 0
  within-document duplicate ids. So the entries are distinct articles, not
  accidental repeats — "uniqueness" is per-RlA-id, not one-per-realia.

Runtime confirmation (loading `Aššur` through `RealiaEntrySchema`): stored 3
RlA entries → API returns only `Aššur A. Stadt`; `B. Land` and `C. Hauptgott`
are dropped.

## Severity

High — silent data loss in API responses for 334 realia entries. No error is
raised, so the loss is invisible without inspecting the data. Bibliography
injection for the dropped entries is also lost.

## Reproduction Steps

1. Point at the `ebldev` database (`.env`: `MONGODB_URI`, `MONGODB_DB`).
2. Query for documents whose `reallexikon` array has size > 1
   (`$expr` + `$size`/`$ifNull`): returns 334 documents (e.g. `Aššur`).
3. Load `Aššur` via `RealiaEntrySchema().load(doc)`:
   `entry.reallexikon` is a single `ReallexikonEntry` (`Aššur A. Stadt`); the
   other two stored entries are gone.

## Recommendation

Revert the data model for `reallexikon` to a list, i.e. undo the modeling
decision of `f13e6daf` while keeping the surrounding ranking/injection work:

- `RealiaEntry.reallexikon: Sequence[ReallexikonEntry] = ()`
- `RealiaEntrySchema.reallexikon` back to
  `fields.List(fields.Nested(ReallexikonEntrySchema), load_default=list)`
  (keep tolerance for a stray single-object value if desired).
- Restore list-based bibliography injection in
  `_collect_reference_ids` / `_inject_reallexikon`.
- Update factory and tests accordingly.

No database migration is required — storage already uses the array shape. The
API response for `reallexikon` returns to an array; the frontend on this
unreleased branch must align on the array shape (the opposite of the note in
`f13e6daf`).

## Resolution

Fix applied (user-approved):

- `RealiaEntry.reallexikon` is a `Sequence[ReallexikonEntry]` again.
- `RealiaEntrySchema.reallexikon` is a `fields.List(fields.Nested(...))`;
  `ReallexikonField` removed; `post_load` restores the tuple.
- List-based bibliography injection restored in `_collect_reference_ids` and
  `_inject_reallexikon`.
- Factory and entry/repository/route tests updated; added regression test
  `test_realia_entry_schema_load_multiple_reallexikon`.

Verified against live `ebldev`: `Aššur` now returns all 3 RlA entries
(A. Stadt / B. Land / C. Hauptgott). Gates: format clean, realia tests pass,
100% coverage on changed source modules, flake8 0, mypy 0.
