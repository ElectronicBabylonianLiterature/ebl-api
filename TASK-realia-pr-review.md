# TASK-realia — PR Review (add-realia)

## Summary

Adds a new `realia` backend module: domain model, marshmallow schemas, a
Mongo repository with three GET endpoints (`/realia/{_id}`,
`/realia/by-id/{realiaId}`, `/realia?query=`), relevance-ranked search, and
bibliography injection. Also extends `query_collation` with a `realia` data
type plus a quote-stripping helper, and tidies `scopes.py` (variable renames
and typo fixes).

Overall the change is well-structured, isolated, and follows existing project
patterns (repository/schema/bootstrap layering mirrors `afo_register`,
`provenance`, etc.). Quality gates pass on the changed code. Findings are
mostly hygiene/process plus a few minor design notes — no correctness
blockers found.

## Gate Results (run locally)

- `flake8` (changed modules, max-line-length=120): PASS (0 errors).
- `mypy` (realia, query_collation, scopes): 0 errors in PR files. The 51
  errors mypy reports are all pre-existing in unrelated modules (corpus,
  fragmentarium, bibliography, ebl_ai_client), surfaced only via
  import-follow.
- Coverage: `ebl/realia/**` = 100% (284 stmts). `scopes.py` = 100%.
  `query_collation.py` new lines (`strip_realia_query_chars`, the `realia`
  branch, `REALIA` enum) are covered; the remaining misses are pre-existing
  lines this PR did not touch.
- Tests: realia/scopes tests pass. Route shadowing, not-found, empty/missing
  query, and cross-reference surfacing are all covered.

## Resolution Status (all findings addressed)

- F1 — RESOLVED. `git rm scripts/seed_realia.py realia-seed-pig.json`.
- F2 — RESOLVED. Removed all 27 `TASK-*` docs plus the Trello-card JSON.
- F3 — RESOLVED. Repository `find()` param renamed `realia_id` -> `id_` in
  the abstract interface and Mongo impl, so `find(id_)` reads distinctly from
  `find_by_realia_id(realia_id)`. URL templates left unchanged — flipping the
  path semantics is a frontend-contract decision and no realia contract is
  present to justify it.
- F4 — ACKNOWLEDGED, no change. The unbounded scan is intentional (the result
  cap was removed deliberately) and acceptable for the small curated
  collection; the regex is escape-safe. Revisit only if realia scales.
- F5 — CONFIRMED intentional. `reallexikon` is a binary richness signal by
  design; left as-is to avoid an unjustified ranking-behavior change.
- F6 — ACKNOWLEDGED, out of scope. The 8 conftest lines are unavoidable (the
  shared `context` fixture must wire `realia_repository`); the 739-line size
  is pre-existing and shared, not introduced here.

Post-change gates re-run: flake8 clean, mypy clean (realia),
`ebl/tests/realia` 60 tests pass at 100% coverage.

## Findings

### F1 — Dev seed artifacts committed (Severity: High / process)

`scripts/seed_realia.py` and `realia-seed-pig.json` were added by this PR, and
the script's own docstring said *"WARNING: Remove this script and any seeded
documents before merging to master."* Removed.

### F2 — Task-tracking docs left in the tree (Severity: Medium / process)

27 `TASK-*` files were added (`TASK-realia-*-{todo,log,review}.md`, plus
`TASK-1-*`, `TASK-715-*`, `TASK-726-*`, `TASK-727-*`, and
`TASK-1-realia_trello_card.json`). The copilot instructions require these to
be removed before a PR is merged; the Trello-card JSON could carry internal
info. Removed.

### F3 — `/realia/{realia_id}` keys on `_id`, not `realiaId` (Low / clarity)

[realia.py:11](ebl/realia/web/realia.py#L11) named the param `realia_id` but
`find()` calls `find_one_by_id` (the Mongo `_id`), while the business
`realiaId` field is served at `/realia/by-id/{realia_id}`. The repository
`find()` parameter is renamed to `id_` so the interface reads clearly; URL
semantics are unchanged pending the frontend contract.

### F4 — Unbounded regex search sorts in Python (Low / performance)

[mongo_realia_repository.py:57-65](ebl/realia/infrastructure/mongo_realia_repository.py#L57-L65):
search runs an unanchored `$regex` (collection scan, not index-served) and the
result cap was removed, so all matches are pulled into memory and sorted in
Python via `RealiaRelevanceRanker`. Fine for a small curated collection;
revisit (Mongo-side sort/limit or a text index) if realia grows. The regex
itself is safe — `CollatedFieldQuery.value` returns `re.escape`d literals plus
controlled character classes, so no injection/ReDoS.

### F5 — `_data_richness` counts reallexikon as a flat +1 (Info)

[realia_search_ranking.py:55-63](ebl/realia/infrastructure/realia_search_ranking.py#L55-L63):
list fields contribute their length, but `reallexikon` adds a constant 1
regardless of size. Confirmed intentional (a binary richness signal).

### F6 — `conftest.py` is 739 lines (Info / pre-existing gate)

The 250-line-per-file hard gate is exceeded by `ebl/tests/conftest.py`, which
this PR appends 8 lines to (new realia fixtures). Pre-existing and shared, so
not introduced here; the additions are unavoidable.

## Reproduction Steps

- Gates: `poetry run flake8 ebl/realia --max-line-length=120`
- Coverage: `poetry run pytest ebl/tests/realia --cov=ebl/realia`
- F1/F2: `git status --short` (now shows the deletions)

## Recommendation

Approve. All findings addressed: F1/F2/F3 fixed in the tree, F4/F5/F6
acknowledged with rationale. No correctness/security/regression blockers.
Remember to remove this review file before merge.
