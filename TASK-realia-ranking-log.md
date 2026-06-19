# TASK-realia-ranking — Work Log

## Problem

Searching `Marduk` did not surface the god's article. Diagnosis (see prior
investigation): the head term `_id: "Marduk"` and the `Divine names` articles
`"Marduk A. …"` / `"Marduk B. …"` exist, but the search matched 73 documents by
unanchored substring, sorted them by `_id`, and truncated to 15. The god landed
at sorted positions 25/26/28 — past the cap.

## Changes

- New `ebl/realia/infrastructure/realia_search_ranking.py`
  - `_FieldMatcher`: for one collation regex, ranks a string as exact (0),
    prefix (1), substring (2), or no match.
  - `RealiaRelevanceRanker`: ranks `_id` matches in tiers 0–2 and
    `relatedTerms`-only matches in tiers 3–5 (`NO_MATCH_RANK = 6` fallback),
    with a case-folded alphabetical `_id` tiebreak. Reuses the same
    `CollatedFieldQuery` patterns as the match filter, so ranking honours the
    existing diacritic collation.
- `ebl/realia/infrastructure/mongo_realia_repository.py`
  - Removed `MAX_SEARCH_RESULTS` and the `.sort("_id").limit(...)`.
  - `search` now fetches all matches and `sorted(...)` them with the ranker
    before schema load + bibliography injection.

## How the ranker works

The ranker turns each matched Mongo document into a sort key; `search` then does
`sorted(documents, key=ranker.key)`, so a lower key means more relevant (higher
in the results).

### `_FieldMatcher` — scores one string against the query

Built once per query from a collation regex pattern, it pre-compiles three
regexes and returns the best tier that fits, or `None`:

```python
self._exact     = re.compile(f"^(?:{pattern})$", re.IGNORECASE)  # whole string
self._prefix    = re.compile(f"^(?:{pattern})",  re.IGNORECASE)  # starts with
self._substring = re.compile(pattern,            re.IGNORECASE)  # anywhere
```

- `0` exact — text equals the query (`"Marduk"`)
- `1` prefix — text starts with it (`"Marduk A. I. …"`)
- `2` substring — it appears somewhere (`"Amêl-Marduk"`)
- `None` — no match

`pattern` comes from `CollatedFieldQuery(query, "_id", "realia").value`, the same
pattern the DB match filter uses, so ranking honours the existing diacritic
collation (e.g. `"Marduk"` still scores `"Mardūk"` as exact).

### `RealiaRelevanceRanker` — combines fields into a key

It holds one `_FieldMatcher` for `_id` and one for `relatedTerms`. `_rank`
returns the `_id` tier when `_id` matches; otherwise the best related-term tier
shifted into a lower band; otherwise the fallback:

```python
id_rank = self._id_matcher.rank(identifier)
if id_rank is not None:
    return id_rank                          # 0,1,2  → _id matches win outright
return TERM_RANK_OFFSET + min(term_ranks)   # 3,4,5  → relatedTerms-only matches
# or NO_MATCH_RANK (6) when nothing matched
```

| Rank | Meaning |
| ---- | ------- |
| 0 | exact `_id` |
| 1 | `_id` prefix |
| 2 | `_id` substring |
| 3 / 4 / 5 | exact / prefix / substring in a `relatedTerms` entry |
| 6 | fallback, no match |

Any `_id` match outranks a `relatedTerms`-only match because the headword is the
most relevant field.

### The sort key

`key()` returns `(rank, identifier.casefold(), identifier)`. Tuple comparison
applies rank first, then — within a tier — case-folded alphabetical `_id`, with
the raw `_id` as a final deterministic tiebreak.

### Worked example (`query="Marduk"`, 73 matches)

- `"Marduk"` → rank 0
- `"Marduk A. I. …"`, `"Marduk B. …"` → rank 1 (prefix)
- `"Amêl-Marduk"`, `"Dûr-Marduk"`, `"Marduk-apla-iddina"` → rank 2, alphabetized

The head article sorts to the top instead of being buried mid-alphabet and cut
off by the old 15-row cap.

`NO_MATCH_RANK = 6` is effectively unreachable in the live flow (a document only
reaches the ranker because the DB filter already matched it) but keeps the ranker
safe to call on any document and is covered directly by a unit test.

## Tests

- `ebl/tests/realia/test_realia_search_ranking.py` (new): exact-first ordering,
  `_id` beats `relatedTerms`, related-term tiers, alphabetical tiebreak,
  diacritic insensitivity, no-match fallback.
- `ebl/tests/realia/test_realia_repository.py`: added
  `test_search_ranks_exact_id_first` and `test_search_has_no_result_limit`
  (20 matches → 20 results).

## Verification

- Live data (read-only): `search("Marduk")` returns all 73 matches; order is
  `Marduk` → `Marduk A. I. …` → `Marduk A. II. …` → `Marduk B. …` → compound
  names. The three `Divine names` articles are present.
- `task format`: clean (also fixed a stray prior-commit format in
  `ebl/tests/factories/realia.py`).
- `task test`: 3578 passed, 2 skipped, 1 xfailed.
- Coverage on both changed source modules: 100%.
- `flake8 --max-line-length=120`: 0. `mypy` on changed files: clean.

## Notes

- Removing the limit is an explicit requirement. A very broad substring query
  now returns every match (loaded via schema + bibliography injection); if this
  becomes a latency issue, consider server-side pagination on the ranked result.
- Pre-existing unrelated `mypy` errors in `ebl/common/domain/scopes.py` remain
  (out of scope; flagged previously).
