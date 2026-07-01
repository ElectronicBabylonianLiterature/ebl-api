# TASK-724 — Realia `wikidataId` served empty for all entries

## Goal

Frontend shows no Wikidata links because `/realia` serves `wikidataId: []` for
every entry. Root-cause and fix the data gap; guard with a load+dump test.

## TODO

- [x] Inspect raw realia document(s) for the wikidata key
- [x] Determine Case A (renamed key) vs Case B (missing/empty) vs data gap
- [x] Confirm schema/repository/route code is correct (round-trips a populated
      `wikidataId`)
- [x] Confirm whether a realia ingestion pipeline / wikidata source mapping
      exists in this repo
- [x] Add a route test asserting a seeded `wikidataId` survives load+dump
- [x] DECISION: the data agent performs the migration by its own means, outside
      this repo. No application-code change is required for the data to surface.
- [x] Removed the in-repo migration tool + its tests (would be unused code in
      the API service): `ebl/io/realia/wikidata_migration.py` and
      `ebl/tests/io/test_realia_wikidata_migration.py`.
- [x] Gates: format / lint / type (pyre) / route test
- [ ] Remind to remove TASK-724 files before merge

## Handoff

Data population is delegated to a separate data agent (its own migration
mechanism). This repo carries only the route-level regression guard. The
lemma→Q-number source mapping and the actual write live outside ebl-api.

## Findings summary

- All 24,361 `realia` docs on `ebldev` have `wikidataId: []` (0 non-empty,
  0 missing the key). Not Case A (no alternate key; `unknown=EXCLUDE` is not
  dropping anything — the key is present and empty).
- No realia ingestion code in this repo (`ebl/io` is fragments-only) and no
  wikidata source mapping (lemma/realiaId → Q-number) anywhere in the repo.
- Schema `wikidata_id -> "wikidataId"` is correct and round-trips a populated
  value (verified directly + existing tests).
- Conclusion: pure data gap; population is blocked on an external source.
