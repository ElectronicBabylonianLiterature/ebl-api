# TASK-realia-ranking-richness — Work Log

## Goal

Introduce a second ranking factor, data richness, used alongside string
matching: within the same string-match tier, prioritise entries that hold more
data.

## Changes

- `ebl/realia/infrastructure/realia_search_ranking.py`
  - `_data_richness(document)`: total item count across `relatedTerms`, `type`,
    `afoRegister`, `references`, `wikidataId`, plus 1 when `reallexikon` is
    present. `reallexikon` is counted as a single binary point (it is unique per
    entry) so the score is identical whether the stored shape is an array
    (production) or a single object (dumped test data).
  - Sort key is now `(match_rank, -richness, casefold(id), id)`: the string-
    match tier stays the primary signal, richness is the tiebreaker, alphabetical
    order is last.

## Tests

- `test_realia_search_ranking.py`: richer entry wins within a tier; richness
  never overrides a better match tier; `reallexikon` array vs. object both count
  as one.
- `test_realia_repository.py`: `test_search_ranks_richer_entry_first_within_tier`
  — the richer entry is alphabetically later, so only richness can float it
  above the sparse one.

## Verification

- Live `search("Marduk")`: exact `Marduk` stays first (richness 102); the
  prefix tier is then ordered by richness (`Marduk-apla-iddina` 12 →
  `Marduk-nādin-aḫḫē` 9 → …), with sparser divine-name articles lower.
- `task format` clean; `task test` 3582 passed, 2 skipped, 1 xfailed.
- Coverage on `realia_search_ranking.py`: 100%.
- `flake8 --max-line-length=120`: 0; `mypy` on changed files: clean.

## Notes

- Interpretation: richness is a secondary factor (string match dominates). An
  exact match always outranks a richer substring match. If a weighted blend is
  wanted instead, the key can be adjusted.
