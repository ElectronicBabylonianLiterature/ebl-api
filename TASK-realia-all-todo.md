# TASK-realia-all — TODO (harden: redirect-stub exclusion)

Extend `GET /realia/all` to exclude pure cross-reference redirect stubs.

Exclude an entry when it has **no own content** AND **exactly one**
`crossReferences` entry. "Own content" = any of: non-empty `afoRegister`;
non-empty top-level `references`; non-empty `afoCrossReferences`; more than one
`reallexikon` entry; or at least one `reallexikon` entry with a non-null
`reference`.

- [ ] Filter stubs in `list_all_realia` via a Mongo `$expr` query, projecting
      only `_id` (no full documents), raw/unencoded ids, sorted.
- [ ] Verify route ordering unchanged (`/realia/all` before `/realia/{id}`).
- [ ] Repo test: pure stub absent; canonical + boundary entries present;
      empty collection -> `[]`.
- [ ] Route test: reserved-char id (e.g. `(Heiliger) Hügel`) returned verbatim.
- [ ] Gates: `task format`, `task test`, 100% coverage on changed files,
      `flake8 --max-line-length=120`, `mypy`, `task lint-md`.

> Remove this file (and `TASK-realia-all-log.md`) before the PR is merged.
