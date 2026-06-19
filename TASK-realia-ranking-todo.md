# TASK-realia-ranking — TODO

Remove the 15-result cap on `GET /realia` search and rank results by relevance
so head terms (e.g. the god "Marduk") surface above compound substring matches.

## Plan

- [x] New module `ebl/realia/infrastructure/realia_search_ranking.py`
      - `_FieldMatcher`: exact / prefix / substring rank for one collation pattern
      - `RealiaRelevanceRanker`: combines `_id` (tiers 0–2) and `relatedTerms`
        (tiers 3–5), alphabetical `_id` tiebreak; uses the same `CollatedFieldQuery`
        patterns as the match filter so matching and ranking stay consistent
- [x] `MongoRealiaRepository.search`: drop `MAX_SEARCH_RESULTS`/`.limit`, sort the
      matched documents with the ranker before loading
- [x] Unit tests for the ranker (all tiers, collation insensitivity, tiebreak,
      no-match fallback)
- [x] Repository tests: ranking order + no cap (>15 matches all returned)
- [x] Pre-commit gates: format, test, coverage, flake8, mypy
- [x] Verify against live data: `search("Marduk")` returns the god article first

## Notes

- No result limit is an explicit requirement; broad substrings may return many
  rows. Flag the perf trade-off.
