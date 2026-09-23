# TASK pr735-fixes — TODO

Address findings D1–D7 from `TASK-pr735-review.md` on PR #735
(`add-realia-slugs-endpoint`).

- [x] Create TODO and log first
- [x] Read repository, schema, cache wiring and existing tests
- [x] D1: explicit `null` array fields must not be listed while the detail
      route cannot load them
- [x] D2: non-string `_id` must not break the listing; malformed entries
      the schema rejects must not be listed
- [x] D3: server-side caching of `/realia/all` (`cache.cached`)
- [x] D4: draft an updated PR description (do not push/edit the PR without
      an explicit request)
- [x] D5: cover the fake `list_non_redirect_ids` line
- [x] D6: draft replies for the two unresolved inline threads (do not post
      without an explicit request)
- [x] D7: mention unrelated changes in the drafted description
- [x] Tests for every change; 100% coverage on changed files
- [x] Gates: format, lint, pyre, pyright, mypy, flake8, full suite, lint-md
- [x] File-length gate (≤ 250 lines)
- [x] Run the service and re-verify the reproduction steps on the final code
- [x] Re-read instructions; report; do not commit
