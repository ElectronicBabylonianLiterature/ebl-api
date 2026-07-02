# TASK-723 / TASK-724 — PR Review (changes since last cleanup)

Reviewed range: `04950fba..HEAD` (commits `9a113627`, `e2b84fa8`).

## Summary

Two changes on `add-realia` since the last cleanup commit:

- **TASK-723** — `GET /realia/<lemma>` now works when the lemma (`_id`)
  contains a `/`. A Falcon sink (`RealiaLemmaSink`) is registered on
  `/realia/(?P<realia_id>.+)`; routes take precedence, so it only catches
  multi-segment (slash-containing) paths. The sink also answers CORS preflight
  `OPTIONS` with `200 + Allow`, fixing a browser "Failed to fetch".
- **TASK-724** — `wikidataId` serves empty for all entries. Root-caused as a
  pure data gap (all 24,361 docs have `wikidataId: []`); serving code is
  correct. Only change kept in-repo is a route-level regression guard test;
  data population is delegated externally.

Verification performed locally:

- `ebl/tests/realia/test_realia_route.py`: 15 passed; **100% coverage** on
  `ebl/realia/web/realia.py` and `ebl/realia/web/bootstrap.py`.
- Full `ebl/tests/realia`: 65 passed.
- `flake8 --max-line-length=120`: clean on all three changed files.
- `mypy` on the two changed source files: no new errors (the ~51 mypy errors
  are pre-existing in 25 unrelated files; project type gate is `pyre`, recorded
  clean in the task log).
- File sizes within the 250-line gate (realia.py 49, bootstrap.py 21, test 198).

Correctness and security of the sink hold up: `find()` uses
`find_one_by_id` (exact-match lookup, not a regex), so the greedy `.+`
capture is not an injection vector; not-found returns 404, non-GET returns 405
with `Allow`, all branches are test-covered.

## Findings

### 1. Task tracking files must be removed before merge — Severity: Medium (process/blocking)

`TASK-723-todo.md`, `TASK-723-log.md`, `TASK-724-todo.md`, `TASK-724-log.md`
are committed on the branch. The Copilot instructions require these to be
removed before a PR is merged, and both todo lists still carry an unchecked
"Remind to remove … files before merge". The branch's own history already
follows this pattern (`04950fba`, `54fc03d9` removed prior artifacts).

**Reproduction:** `git show --stat HEAD` / `ls TASK-*.md` shows the four files
tracked.

**Recommendation:** delete the four `TASK-72{3,4}-{todo,log}.md` files (and this
review file) before merge.

### 2. GET handling duplicated between resource and sink — Severity: Low (cleanliness)

`RealiaLemmaSink.__call__` (realia.py:29-30) repeats `RealiaResource.on_get`
(realia.py:11-13) verbatim (`find` + `RealiaEntrySchema().dump`). If the serving
logic changes, both must be updated in lockstep.

**Recommendation (optional):** have the sink delegate to the resource's GET
path (e.g. call `self._resource.on_get(...)` or a shared helper) so there is a
single source of truth. Not blocking — both are two lines.

### 3. `_allowed_methods` class attribute declared after `__init__` — Severity: Low (style)

realia.py:20 places the class attribute below `__init__`. Functionally fine;
conventional placement is at the top of the class body for readability.

## Informational (no action)

- TASK-724 ships only a regression-guard test, which is the correct scope: the
  API serving path already round-trips a populated `wikidataId`. Confirmed the
  in-repo migration tool + tests were removed (they would be unused code in the
  API service). The external data-population handoff is documented in the log.
- Sink/route interaction: an unusual path like `/realia/by-id/A/B` (a slash
  inside a by-id value) would fall through to the sink and 404, since the
  single-segment by-id route can't match it. Acceptable edge case; not a
  regression.

## Recommendation

Approve the code changes — correctness, coverage, lint, and types are green,
and the sink approach is sound and well-verified. **Blocking item before
merge:** remove the four TASK tracking files (Finding 1). Findings 2 and 3 are
optional cleanups.
