# TASK-realia-ranking — Review

## Summary

`GET /realia` search returned at most 15 alphabetically-sorted substring matches,
so head terms were buried (the god "Marduk" never appeared). Removed the result
cap and added a relevance ranker that orders exact `_id` matches first, then
prefix, then substring, then `relatedTerms`-only matches, with an alphabetical
tiebreak.

## Findings

1. **15-result cap + plain `_id` sort dropped relevant matches.**
   Severity: High (results unfindable). Status: fixed (cap removed).
2. **No relevance ranking; substring hits ranked equal to head-term hits.**
   Severity: High. Status: fixed (ranker added).
3. **No limit means broad queries return all matches (latency).**
   Severity: Low. Status: accepted per requirement; flagged.

## Severity

- Findings 1 & 2 made legitimate articles undiscoverable via search — the
  reported "Marduk" symptom.

## Reproduction Steps

1. Point the API at the real `ebldev` database.
2. `GET /realia?query=Marduk`.
3. Before: 15 results, all `*…`/`A`–`I` compound names; no `Marduk` head article.
4. After: 73 results; order `Marduk` → `Marduk A. I.` → `Marduk A. II.` →
   `Marduk B.` → compounds.

## Recommendation

- Findings 1 & 2: ship (done).
- Finding 3: if broad queries become slow in production, add server-side
  pagination over the ranked results (keep ranking server-side, page the
  output). No change made now, per the explicit "no limit" requirement.

## Cleanup reminder

Before merge, remove the task tracking files for this task
(`TASK-realia-ranking-*.md`) and the earlier `TASK-realia-search-*.md` /
`TASK-719-*.md` files.
