# TASK pr735-address — Log

## 2026-09-23

- Created TODO and log before any work.
- Findings to address (from the rereview of `6394de8d`): F1 8 TASK `.md`
  files committed in the PR; F2 Fabdulla1's review and two threads
  unanswered; F3 `CACHE_CONFIG` unknown in production; F4 detail route 500 on
  malformed entries (pre-existing).
- The rereview's full test run was cut off at ~60% when the previous session
  ended (`PluggyTeardownRaisedWarning: OSError: cannot send`); it is void and
  is being rerun.
- F1: `git rm --cached` on the 8 `TASK-pr735-*.md` files that
  `origin/master...HEAD` adds. Working copies kept (now untracked). Staged vs
  `HEAD`: exactly 8 deletions. Index vs merge base: 14 files, no `.md`
  added (README modified only). Not committed.
- **Error I made:** my first verification diffed the index against the
  `origin/master` tip instead of the merge base, which listed master's newer
  commits in reverse and looked like mass deletions. Nothing was wrong in
  the index; reran against the merge base.
- F3: `infrastructure/ebl.yml` (org repo) sets production
  `CACHE_CONFIG: '{"CACHE_TYPE": "redis", "CACHE_REDIS_HOST": "redis"}'`.
  Verified locally with a throwaway `redis:7-alpine` container on
  `127.0.0.1:6379` and two app processes (8738, 8739) on DB
  `ebl_review_pr735c`: 6 alternating GETs → 1 `realia` query, one shared
  memoize key (TTL 600), identical bodies, `Cache-Control` on every
  response. No code change needed; the finding is resolved. Servers
  stopped (144 = my kill), container stopped, DB dropped (verified).
- F2/F4: drafts below. Not posted; posting needs an explicit request.

## Drafts (not posted)

### F2 — reply to Fabdulla1's 2026-08-18 review

Thanks, all three points are addressed in `6394de8d`:

- **Explicit `null`:** the listing now keeps only entries that
  `RealiaEntrySchema` can load (`realia_loadability.py`), which is the same
  load `/realia/{id}` performs. Explicit `null` in list fields, a `null`
  `realiaId` and wrong-shaped elements are no longer listed, and non-string
  `_id`s are filtered in the query. `realia_document_shape.py` is gone.
  Tests: `test_realia_list_loadability.py`.
- **Caching:** the ID list is memoized through the app cache
  (`cache.memoize`, 600 s) and `Cache-Control` is still sent on every
  response. `cache.cached` isn't used because a cache hit skips the after
  hooks and drops the header; the README now documents this. With the
  production Redis backend, repeated calls across workers run one query per
  600 s. Test: `test_list_is_cached_server_side`.
- **PR description:** rewritten to match the final behaviour.

Could you take another look?

### F2 — reply on the `bootstrap.py` thread

The route is back on `/realia/all`, so `ids` is no longer involved. `all` is
reserved in `ebl/realia/domain/reserved_identifiers.py`, which both the route
and the listing exclusion use. The API has no Realia create or import path to
enforce it at write time, so the PR description documents it as an accepted
constraint (such an entry is reachable only via `/realia/by-id/{realiaId}`).

### F2 — reply on the `realia_stub_filter.py` thread

Done: every array access in the stub filter goes through `_as_array`
(`$cond` + `$isArray`), and the listing also keeps only entries
`RealiaEntrySchema` can load, so a scalar, object or `null` in any field
neither breaks the query nor gets listed. Covered by
`test_realia_stub_filter_robustness.py` and
`test_realia_list_loadability.py`.

### F4 — follow-up issue

Title: Realia detail route returns 500 for entries the schema cannot load

`GET /realia/{id}` returns 500 when the stored document fails
`RealiaEntrySchema` validation, for example `type: null` raises
`ValidationError: {'type': ['Field may not be null.']}`. Reproduced locally
on the PR #735 head, whose detail route runs the same `find` and schema
load as `master` (the PR only renames the parameter): seed
`{"_id": "NullType", "crossReferences": [], "type": null}` and request
`/realia/NullType`. `GET /realia/all` (PR #735) already leaves such entries
out. Options: clean the legacy documents in the data, or map a load
`ValidationError` to a clearer response. Needs a decision on which.

- **Error I made:** the first F4 draft claimed a reproduction on `master`;
  it was on the PR head. Corrected the wording above.

## Gates

- Full suite `poetry run pytest -n auto`: 4443 passed, 2 skipped, 1 xfailed,
  exit 0 (6 min). No `.py` changed in this task, so format, lint, pyre,
  pyright, mypy, flake8 and coverage results from the rereview (same code,
  `6394de8d`) still apply.
- `task lint-md`-equivalent on every `TASK-pr735-*.md`: 0 errors.
- Re-read the copilot instructions before reporting. Nothing committed,
  pushed or posted. Staged: 8 deletions only.
