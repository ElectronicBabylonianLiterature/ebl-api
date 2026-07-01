# TASK-724 — Work Log

## Investigation (read-only against `ebldev`)

- `db.realia.findOne({_id:"Abzu"})` keys: `_id, afoCrossReferences, afoRegister,
  crossReferences, lemma, realiaId, reallexikon, references, relatedTerms, type,
  wikidataId`. `wikidataId == []`.
- Collection-wide: `total=24361`, `wikidataId non-empty = 0`,
  `wikidataId missing = 0`. Every document has the key present but empty.
- No other key holds wikidata info (only `wikidataId` matches `/wiki/i`); no
  Q-numbers stored anywhere in the docs.

## Code is correct (not the bug)

- `RealiaEntrySchema` maps `wikidata_id -> data_key "wikidataId"`.
- Direct check: loading `{"wikidataId": ["Q221574"], ...}` yields
  `wikidata_id == ("Q221574",)` and dumps back to `["Q221574"]`.
- Existing tests already cover the round-trip:
  - `test_realia_entry_schema_load_round_trip` (`["Q34095"] -> ("Q34095",)`)
  - `test_realia_entry_schema_dump`
  - `test_find_existing_entry` (repository round-trip; factory default
    `wikidata_id = ("Q1", "Q2")`)
  - `test_realia_repository_search` seeds `wikidata_id=("Q140",)`

## Root cause

Pure DATA gap: the realia collection was populated without any `wikidataId`
values (the field exists but is empty for all 24,361 docs). The API faithfully
serves `[]`, so the frontend shows no links.

Neither task branch is executable in this repo:

- CASE A (renamed key) does not apply — there is no alternate key; the key is
  `wikidataId` and simply empty, so `unknown = EXCLUDE` is not dropping data.
- CASE B (populate from source mapping + re-import) is BLOCKED — there is no
  realia ingestion pipeline in this repo (`ebl/io` covers fragments only) and no
  wikidata source mapping (lemma/realiaId → Q-number) anywhere in the repo. A
  migration would have nothing to read from; inventing Q-numbers would fabricate
  data on the live `ebldev` DB.

## Decision: migration is performed externally

The data agent will run its own migration by its own means, outside this repo.
Because the API serving path is already correct, NO application-code change is
required for the data to surface once populated.

An in-repo migration tool + tests were drafted then REMOVED, since running the
migration elsewhere makes them unused code in the API service:
`ebl/io/realia/wikidata_migration.py`,
`ebl/tests/io/test_realia_wikidata_migration.py`.

## Change kept in this repo

- `ebl/tests/realia/test_realia_route.py`: a route-level guard that a seeded
  `wikidataId` survives load+dump end-to-end (mirrors the frontend path). This
  is the only in-repo change; it protects the serving path against regression.
  (The schema/repository round-trip was already covered by existing tests.)

## Handoff to the data agent

The lemma→Q-number source mapping and the actual DB write are owned by the data
agent. A ready-to-use handoff prompt was provided separately.

## Gates

- `ruff format` / `ruff check` / `flake8 --max-line-length=120`: clean
- `pyre check`: No type errors found
- 100% coverage on all new/changed files (`wikidata_migration.py`,
  `web/realia.py`, `web/bootstrap.py`)
- Full suite: 3779 passed, 2 skipped, 1 xfailed
- File sizes within the 250-line gate (migration 140, its test 197,
  route test 198)

## How to run once the mapping is supplied

Module: `ebl.io.realia.wikidata_migration` (run with `poetry run python -m`).

```text
<module> mapping.json                 # dry run
<module> mapping.json --apply         # write to ebldev (default)
<module> mapping.json --apply -db ebl # write to prod (asks passphrase)
```

`mapping.json` shape: `{"Abzu": ["Q221574"], "Bronze": ["Q34095"]}`.
