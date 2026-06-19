# TASK-realia-ranking-richness — TODO

Add a second ranking factor — data richness — used alongside string matching.
Within the same string-match tier, entries with more data rank higher.

## Plan

- [x] `RealiaRelevanceRanker`: add `_data_richness(document)` = total item count
      across `relatedTerms`, `type`, `afoRegister`, `references`, `wikidataId`,
      plus 1 if `reallexikon` is present (unique, so 0/1; robust to the stored
      array vs. dumped single-object shape)
- [x] Sort key becomes `(match_rank, -richness, casefold(id), id)` — match tier
      stays primary, richness is the tiebreaker before alphabetical
- [x] Unit tests: richer entry wins within a tier; richness never overrides a
      better match tier
- [x] Repository integration test for richness ordering
- [x] Gates: format, test, coverage, flake8, mypy
- [x] Verify on live data
