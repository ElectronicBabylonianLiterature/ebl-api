# TASK realia-info — TODO

Embed realia display titles (`realiaInfo`) in the fragment GET response.

- [ ] `RealiaInfo` domain object (`realia_id`, `lemma`, `type`).
- [ ] `RealiaInfoSchema` (`realiaId`, `lemma`, `type`) with `data_key`s.
- [ ] `resolve_realia_info(fragment, realia_repository)` — distinct realiaIds,
      single batch load, project `{realiaId, _id→lemma, type}`, dangling omitted.
- [ ] Batch `find_by_realia_ids` on `RealiaRepository` + Mongo impl (single `$in`).
- [ ] `create_response_dto` accepts optional `realia_info`; field emitted only on
      read (omitted on writes via existing `filter_none`).
- [ ] `FragmentsResource.on_get` computes `realia_info`; bootstrap injects repo.
- [ ] Update existing `test_get` to expect `realiaInfo: []`.
- [ ] New tests: route (per-distinct-id, dedup, dangling, empty), write
      round-trip (no 422 / not emitted / not stored), resolver, schema, repo.
- [ ] Gates: `task format`, `task test`, 100% coverage on changed files,
      `flake8 --max-line-length=120`, `mypy --ignore-missing-imports`.

Remove this file and `TASK-realia-info-log.md` before the PR is merged.
