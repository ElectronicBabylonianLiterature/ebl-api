# TASK-realia-ranking-richness — Review

## Summary

Added data richness as a second ranking factor alongside string matching.
Within a string-match tier, entries with more data now rank higher; the match
tier remains primary and alphabetical order is the final tiebreak.

## Findings

1. **Only string matching drove ranking; equally-matched entries fell back to
   alphabetical order.** Severity: enhancement. Status: implemented — richness
   tiebreaker added.
2. **`reallexikon` stored shape differs (array in production, single object in
   dumped test data).** Severity: Low (correctness of the metric). Status:
   handled — counted as a single binary point, identical for both shapes.

## Severity

- Behavioural enhancement requested by the user; no pre-existing bug.

## Reproduction Steps

1. `GET /realia?query=Marduk`.
2. Before: prefix matches (`Marduk A. …`, `Marduk-apla-iddina`, …) ordered
   alphabetically.
3. After: exact `Marduk` first, then prefix matches ordered by data richness
   (most-populated entries first).

## Recommendation

- Ship (done). Richness is a secondary factor by design — an exact match still
  outranks a richer substring match. Revisit to a weighted blend only if product
  wants richness to influence across tiers.

## Cleanup reminder

Before merge, remove `TASK-realia-ranking-richness-*.md` together with the other
`TASK-*` artifacts.
