# TASK-realia-cross-references — Review

## Summary

Exposed the resolved Realia cross-reference fields end-to-end and added
stable-id navigation. The `realia` collection now carries resolved
cross-references plus the AfO volume/page on each entry; the API previously
dropped them via `unknown = EXCLUDE`, so the frontend could not build links.
Added `realiaId`, `crossReferences` (`{id, lemma}`), `afoCrossReferences`
(`{id, lemma, afoVolume, page}`), and on each `afoRegister` entry `afoVolume`,
`page`, and `crossReferences`. Added `GET /realia/by-id/{realiaId}` keyed on
the stable `realiaId` while keeping the lemma-keyed `GET /realia/{id}` for
backward compatibility.

This review also audits the change against the repo Copilot instructions
(250-line hard gate, 100% coverage on touched files, lint/type gates) and
records the fixes applied.

## Findings

1. **New fields surfaced without silently dropping them.** Added explicit
   marshmallow fields + domain attributes for `realiaId`, `crossReferences`,
   `afoCrossReferences`, and `afoRegister[].{afoVolume,page,crossReferences}`.
   Lists default to `[]`; cross-reference objects require `id`+`lemma`; AfO
   cross-references additionally require `afoVolume`+`page`.
   Severity: High (feature). Status: implemented.
2. **Stable-id lookup added.** New `find_by_realia_id` queries
   `{"realiaId": ...}`; new `RealiaByIdResource` and route
   `/realia/by-id/{realia_id}` registered before `/realia/{realia_id}`.
   Falcon 3.1.3 prefers the literal `by-id` segment over the field template,
   verified by routing test.
   Severity: High (feature). Status: implemented.
3. **250-line hard gate violation (Copilot instructions).** The feature pushed
   three files over 250 lines: `mongo_realia_repository.py` (270),
   `test_realia_entry.py` (316), `test_realia_repository.py` (267).
   Severity: High (gate). Status: fixed — extracted
   `realia_schemas.py`; split tests into `test_realia_cross_references.py` and
   `test_realia_repository_search.py`; shared seeding helpers moved to
   `realia_repository_helpers.py`. All files now < 200 lines.
4. **Backward-compat note: a lemma literally named `by-id` is shadowed** by the
   new route. Acceptable per the task (the new route shape was requested) and
   no such lemma exists in the data.
   Severity: Info. Status: accepted, documented here.
5. **No index on `realiaId`.** `find_by_realia_id` does a collection scan. The
   realia collection is a small reference dataset and `find` on the existing
   `_id` is the hot path; left unindexed to mirror the current repository
   (no `create_indexes`). Worth revisiting if link traffic grows.
   Severity: Low. Status: accepted, documented here.
6. **Search ranking unchanged.** `RealiaRelevanceRanker` uses a fixed richness
   field list, so the new fields do not alter result ordering.
   Severity: Info. Status: intentional, no change.

## Severity

- Findings 1–3 are the substantive items: the feature itself and the mandatory
  250-line refactor. All implemented/fixed and gated.
- Findings 4–6 are accepted trade-offs documented for the reviewer.

## Reproduction Steps

1. `poetry run pytest ebl/tests/realia/` → 51 passed.
2. Load a stored doc with the new shape; confirm `RealiaEntrySchema` surfaces
   `realiaId`, `crossReferences`, `afoCrossReferences`, and enriched
   `afoRegister[].crossReferences` (see
   `test_realia_entry_schema_load_cross_references`).
3. `GET /realia/by-id/realia_003277` for `Elam (Geschichte)` returns 200 with
   `_id` = "Elam (Geschichte)" and `realiaId` = "realia_003277" (see
   `test_get_realia_by_realia_id`).
4. Validation: omitting `id`/`lemma` (or `afoVolume`/`page` on AfO refs) raises
   `ValidationError` (see `test_realia_cross_references.py`).

## Recommendation

Merge. Gates verified: `black` clean, `ruff` clean,
`flake8 --max-line-length=120` clean, `mypy` (changed files) and `pyre` clean,
full suite 3752 passed / 0 failed, 100% coverage on all changed source
modules. Before merging the PR, remove the `TASK-realia-cross-references-*.md`
tracking files and the dev-only seed script/data if no longer needed.

## Whole-PR Review (branch `add-realia` vs `master`)

Scope: the entire new Realia module (domain, schemas, repository, web,
search ranking, tests, factories) plus shared edits to `app.py`, `context.py`,
`tests/conftest.py`, `common/domain/scopes.py`, and
`common/query/query_collation.py`, and the dev-only seed script/data.

Two independent review passes (domain/schema/repo and web/ranking/tests) were
run in addition to a manual review of the shared files. Findings, triaged:

### Acted on (code changes)

- **AfoCrossReference contract was self-contradictory** — domain defaulted
  `afo_volume`/`page` to `""` while the schema marked them `required=True`.
  Made the domain fields required to match the schema and the data contract.
- **Search regex injection** — proven safe (`re.escape` in
  `CollatedFieldQuery`); locked in by
  `test_search_treats_regex_metacharacters_literally` (`.*`, `Li.n`, `(a+)+`
  all match nothing).
- **`realiaId` uniqueness** (was deferred, now fixed) —
  `MongoRealiaRepository.create_indexes()` declares a **partial unique index**
  on `realiaId` with `partialFilterExpression={"realiaId": {"$gt": ""}}`, so
  unique is enforced only for non-empty ids (empty/missing `realiaId` docs,
  which the schema dumps as `""`, are excluded). Wired into the route
  bootstrap and the abstract repository. Covered by three tests (declares
  partial-unique, rejects duplicates, allows blank/missing).
- **`_inject_references` simplification** — replaced the
  dump-then-reload-through-`ApiReferenceSchema` round-trip with
  `reference.set_document(...)` plus a shared `_document_for` helper that runs
  `create_object_entry` (the only transformation the round-trip performed).
  Same behaviour, less fragility; verified by existing injection tests.
- **Defensive `_rank`** — guards non-list `relatedTerms` (matches the existing
  `_data_richness` guard), with a unit test.
- **`Unexepcted` → `Unexpected`** typo fixed in `scopes.py` and its test.

### Added tests

- Duplicate `realiaId` rejected; blank/missing `realiaId` allowed.
- Lemma named `by-id` still resolves through `/realia/by-id` (not shadowed).
- Whitespace-only search query returns `[]`.
- Diacritic tiebreak is deterministic; multi-element `reallexikon` still
  contributes a flat richness of 1; non-list `relatedTerms` treated as empty.

### Accepted / documented (by design, no code change)

- **Reallexikon reference load is intentionally lean.**
  `ReallexikonReferenceField._deserialize` builds a `DISCUSSION` `Reference`
  from the stored `{id, pages}` shape. The stored data carries only `id` and
  `pages` (the documented lean-reference contract from the prior reallexikon
  task), so there is nothing to preserve; this is not a regression.
- **Response uses `_id`** (via `data_key="_id"`) rather than `id`. Intentional
  and required by the frontend, which keys cross-reference links on the lemma
  `_id`. Per the repo "backend schema is the source of truth" rule, no alias
  is introduced.
- **Dangling bibliography reference** yields `document={}`; the schema's
  `data["document"] and create_object_entry(...)` short-circuits on the empty
  dict, so there is no crash. Verified.
- **Shared edits are clean.** `scopes.py` renames locals (avoids shadowing the
  `prefix`/`suffix` properties); `query_collation.py` additively introduces
  the `realia` data type, strip helper, and field config;
  `app.py`/`context.py`/`conftest.py` wire the repository like the other
  collections. No behaviour change to unrelated collections.

### Verdict

Merge. All review findings are now either fixed or documented as deliberate
design decisions; no open items remain.
