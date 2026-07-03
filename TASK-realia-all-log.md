# TASK-realia-all — Work Log (harden: redirect-stub exclusion)

## Task

Extend the existing `GET /realia/all` to exclude pure cross-reference redirect
stubs, so redirecting URLs don't land in the sitemap. Reproduce the frontend's
`hasOwnContent` / `getRedirectTarget` rule on the backend.

Exclude when: **no own content** AND **exactly one** `crossReferences` entry.
Own content = any of: non-empty `afoRegister`; non-empty top-level `references`;
non-empty `afoCrossReferences`; more than one `reallexikon` entry; or at least
one `reallexikon` entry with a non-null `reference`.

## Findings

- Stored field names (camelCase) confirmed in `realia_schemas.py`:
  `afoRegister`, `references`, `afoCrossReferences`, `reallexikon` (each with a
  `reference` that is `null` or a dict), `crossReferences`.
- A stored `reallexikon.reference` is only ever `null` or a dumped Reference dict
  (which always carries an `id`), so a raw Mongo `reference != null` check
  matches the domain's `reference is not None` for real data — no empty-dict /
  empty-string edge cases occur in stored documents.
- Test DB is a real in-memory `mongod` (`pymongo_inmemory`), so `$expr` /
  `$filter` / `$ifNull` / `$size` are available.
- Factory defaults give every seeded entry a non-empty `afoRegister` (2 entries),
  including `insert_minimal`, so all pre-existing seeded entries have own content
  and remain listed — existing tests stay green.
- OpenAPI docs (`docs/openapi`) only cover partner-bibliography; no spec change.

## Steps

1. `list_all_realia` now runs `find({"$expr": <listable>}, projection={"_id":
   True})` and returns `sorted(_id)`. Only `_id`s cross the wire (no full
   documents); ids are raw / unencoded; order is deterministic.
2. `<listable>` = `has_own_content OR crossReferences count != 1`, i.e. the exact
   negation of the redirect-stub rule. Built from small helpers
   (`_has_own_content_expression`, `_array_size`, `_reallexikon_reference_count`).
3. Route registration unchanged — `/realia/all` still added before
   `/realia/{realia_id}` and the slash sink.
4. Tests:
   - `test_list_all_realia_excludes_redirect_stubs` (repo) seeds two stubs
     (empty; reallexikon-stub-only) and seven listable entries exercising every
     own-content branch plus zero/two cross-references; asserts stubs absent and
     the listable set present.
   - `test_list_all_realia_returns_ids_verbatim` (route) asserts an id with
     reserved chars (`(Heiliger) Hügel`) is returned unencoded.
   - Existing repo/route/empty/no-cap/shadow tests unchanged and still green.

## Gate results

- `ruff format` — unchanged.
- `flake8 --max-line-length=120` — clean.
- `mypy --follow-imports=silent` on changed files — no issues.
- Coverage — 100% on all 4 changed realia modules.
- File-size gate — all touched files < 250 lines.
- `task lint-md` — 0 errors.
- `task test` — full suite (see terminal).
