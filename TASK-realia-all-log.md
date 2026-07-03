# TASK-realia-all — Work Log

## Context

Frontend `add-realia-slugs` calls `GET /realia/all` (returns `string[]`) for
sitemap generation. Backend must return every Realia entry's `_id` (the
navigation key equal to the lemma), not `realiaId`. Mirror the
`/signs/all` + `/bibliography/all` "list all" pattern.

## Findings

- `RealiaRepository` at `ebl/realia/application/realia_repository.py`.
- Mongo impl at `ebl/realia/infrastructure/mongo_realia_repository.py`.
- Web resources at `ebl/realia/web/realia.py`; routes registered in
  `ebl/realia/web/bootstrap.py`.
- Signs pattern: `SignsListResource.on_get` -> `list_all_signs()` ->
  `self._collection.get_all_values("_id")`. `/signs/all` registered before
  `/signs/{sign_name}`.
- A Falcon sink handles realia lemmas with slashes; explicit `add_route`
  takes precedence over the sink and over the templated route.
- OpenAPI docs (`docs/openapi`) only cover partner-bibliography; neither
  `/signs/all` nor realia routes are documented there -> no spec change.

## Steps

1. `RealiaRepository.list_all_realia() -> Sequence[str]` (abstract) +
   `MongoRealiaRepository.list_all_realia` returns
   `sorted(self._realia_collection.get_all_values("_id"))` — projects `_id`
   only via Mongo `distinct`, deterministic (sorted) for reproducible sitemaps.
2. `RealiaListResource.on_get` sets `resp.media` to the id list.
3. Registered `api.add_route("/realia/all", realia_list_resource)` first, so
   the static `all` segment wins over `/realia/{realia_id}` and the sink.
4. Tests: repo `test_list_all_realia` (seeded, sorted) + `_empty` (`[]`);
   route `test_list_all_realia` (200 + array) + `_is_not_shadowed_by_id`
   (empty collection returns 200 `[]` not 404 — proves it hits the list
   resource, not `find("all")`). Auth: same unauthenticated `client` fixture
   as every other realia route test, matching `/signs/all`.

## Gate results

- `task format` — 729 files already formatted (no changes).
- `flake8 --max-line-length=120` on 4 changed modules — clean.
- `mypy --follow-imports=silent` on 4 changed modules — no issues. (Full-repo
  mypy reports 51 pre-existing errors in unrelated modules, none in changed
  files; not introduced here.)
- Coverage — 100% on all 4 changed modules.
- File-size gate — all touched files < 250 lines.
- `task test` — full suite (see terminal).

