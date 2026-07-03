# TASK-realia-all — TODO

Add `GET /realia/all` endpoint returning a JSON array of all Realia `_id`s.

- [ ] Add `list_all_realia` to `RealiaRepository` (abstract) and
      `MongoRealiaRepository` (project `_id`, sorted for deterministic output).
- [ ] Add `RealiaListResource` web resource returning the id array as JSON.
- [ ] Register `GET /realia/all` before `GET /realia/{realia_id}` in the
      realia bootstrap so `all` is not captured as an `{id}`.
- [ ] Repository test: all ids from seeded fixtures; empty collection -> `[]`.
- [ ] Route test: `200` + JSON array; `all` not misrouted to `{id}` handler;
      auth matches other realia routes.
- [ ] Run pre-commit gates: `task format`, `task test`, coverage (100% on
      changed files), `flake8 --max-line-length=120`, `mypy`.

> Remove this file (and `TASK-realia-all-log.md`) before the PR is merged.
