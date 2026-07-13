# TASK-realia-all — TODO

## Feature: `GET /realia/all`

- [x] Add `GET /realia/all` returning every Realia id, sorted.
- [x] Exclude redirect stubs (entries whose only content is one cross-reference).
- [x] Diagnose why the committed stub-exclusion excluded nothing on live data.
- [x] Fix the reference check to match the domain rule (dict needs a non-empty
      `id`; string must be non-empty).
- [x] Verify against the live 24k dataset: 0 disagreements vs the domain rule.
- [x] Extend repo test with dict-without-id / empty-string / string reference.

## Review round (PR #735)

- [x] Fetch and address all existing PR feedback (Sourcery: 2 comments).
- [x] Sourcery 1 — rename the misleading `list_all_realia`. Rejected the
      "return `Sequence[RealiaEntry]`" variant: it would load 24k documents and
      run bibliography injection just to project `_id`.
- [x] Sourcery 2 — the route test seeded already-sorted ids, so it could not
      detect broken sorting. Seed unsorted and assert the sorted result.
- [x] Name the load-bearing `reallexikon > 1` threshold and restate the filter as
      "a redirect stub is an entry whose only content is a single
      cross-reference".
- [x] Prove the `$expr` refactor is behaviour-preserving on live data.
- [x] Remove the task artifacts that commit `ca7b8d3c` re-added.
- [x] Gates: `task format`, `task test`, 100% coverage on changed files,
      `flake8 --max-line-length=120`, `mypy`, `task lint-md`, files < 250 lines.

## Open — contract decisions for the API owner, not changed here

- [ ] `/realia/all` returns 24,340 of 24,361 entries; the name says "all".
- [ ] `/realia/all` shadows any entry whose `_id` is literally `all` (none today).

> Remove this file (and `TASK-realia-all-log.md`, `TASK-realia-all-review.md`)
> before the PR is merged.
