# TASK-realia-reallexikon — Review

## Summary

RlA (reallexikon) entries are unique per realia entry, so the list model was
excessive. `reallexikon` is now a single `Optional[ReallexikonEntry]`; the
Marshmallow field bridges the stored array (no migration) and the API exposes an
object|null.

## Findings

1. **`reallexikon` modelled as a list though always 0 or 1 in real data.**
   Severity: Low (correctness/clarity). Status: fixed — single optional entry.
2. **API response shape changes from array to object|null.**
   Severity: Info. Status: accepted on this unreleased branch; frontend must
   align.

## Severity

- No runtime bug; this is a model-fidelity/contract simplification driven by the
  actual data distribution.

## Reproduction Steps

1. Inspect the live `realia` collection: 15,422 docs with 0 reallexikon, 9,750
   with 1, 1 with 3 (the "Pig" seed).
2. Before: `reallexikon` was a tuple; consumers indexed `[0]`.
3. After: `find`/`search` expose a single `ReallexikonEntry` or `None`.

## Recommendation

- Ship (done). Coordinate the frontend to read `reallexikon` as object|null.
- When the "Pig" seed is deleted before merge, the only multi-entry document
  disappears; nothing else relies on more than one.

## Cleanup reminder

Before merge, remove the task tracking files
(`TASK-realia-reallexikon-*.md`) along with the other `TASK-*` artifacts.
