# TASK-735 Review — PR #735: Add Realia ID listing endpoint

> **Status update.** All findings below were addressed in the working tree
> (uncommitted). See `TASK-735-fix-log.md` for what changed and why.
> Two items are **superseded** and two need a decision from the user:
>
> - **Finding 1 is superseded.** The review recommended renaming the route
>   off the entry namespace. That is not available: `ebl-frontend` master
>   already calls `GET /realia/all` (merged in frontend PR #762 on
>   2026-08-11), so the route was restored to `/realia/all` and the
>   collision was solved structurally instead — reserved identifiers are
>   excluded from the listing, so no unreachable ID is ever emitted.
> - **Finding 8 was partly wrong.** Removing `or ""` and the `cast(...)`
>   calls produces 5 pyright errors; they are required. Only the `IF_NULL`
>   inlining was valid, and it fell out of the Finding 2 fix.
> - **Finding 5 still needs a domain decision** — behaviour is unchanged;
>   only the constant was renamed.
> - **Finding 4 not applied** — editing the PR title/body is an
>   outward-facing action and is awaiting the user's authorisation.
>
> One additional defect was found during re-verification and fixed: the
> listing could emit an ID whose entry route returns 500. See
> "Post-fix addendum" at the end of this file.

- PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735>
- Branch: `add-realia-slugs-endpoint` → `master`
- Head reviewed: `924340f019ea5fc260c1534ef1242ff88ad07dca`
- State: OPEN, **mergeable: CONFLICTING**, 11 files, +388 / -4

## Summary

The PR adds `GET /realia/ids`, returning a JSON array of Realia `_id`s for
frontend sitemap generation. It adds `list_non_redirect_ids` to the
repository interface and its Mongo implementation, a `$expr` filter that
excludes bare redirect stubs (`realia_stub_filter.py`), an accent- and
case-insensitive sort helper (`realia_id_sorting.py`), a
`RealiaListResource` with a public cache header, and two new test modules.

The engineering quality of the feature itself is good. Every CI check is
green, every local gate passes, coverage on the changed modules is 100%,
and the live route behaves as intended for well-formed data. Both Sourcery
comments are genuinely addressed.

However **the PR is not mergeable as it stands**. Two reviewer comments
from `Fabdulla1` dated 2026-07-29 are still open, and I reproduced both
against a running instance — one of them causes a hard `500` on the new
endpoint. Two `CHANGES_REQUESTED` reviews remain unresolved, three files
conflict with master, and the PR title and description still describe the
old `/realia/all` design.

## Existing PR feedback — status

Fetched via `gh api` for reviews, inline diff comments, and issue
comments. No merge commits exist on this branch, so there is no merged-in
PR whose feedback also needed fetching.

1. **Sourcery, inline on `realia_repository.py`** — `list_all_realia`
   returning `Sequence[str]` is inconsistent with `search`; rename it or
   return domain objects.
   **Addressed.** Renamed to `list_non_redirect_ids`; the ID-only intent
   is now explicit.
2. **Sourcery, inline on the route test** — the test should assert sorted
   order rather than insertion order.
   **Addressed.** `test_list_ids_returns_sorted_ids` seeds
   `Pig, Anu, Enlil, Ellil` and asserts sorted output.
3. **Fabdulla1, review of 2026-07-22 (CHANGES_REQUESTED)** — `/realia/all`
   shadows an entry whose `_id` is `"all"`.
   **Addressed.** Route renamed to `/realia/ids`;
   `test_entry_named_all_is_reachable` covers it; verified live —
   `GET /realia/all` returns 200 and the entry.
4. **Fabdulla1, inline of 2026-07-29 on `bootstrap.py`** — the rename
   moves the collision to `"ids"`, and `realiaId` may be blank so
   `/realia/by-id/...` is not a guaranteed fallback.
   **OPEN.** Reproduced — see Finding 1.
5. **Fabdulla1, inline of 2026-07-29 on `realia_stub_filter.py`** —
   `$size`/`$filter` after `$ifNull` do not protect against legacy
   documents where an array field holds a scalar or object; guard with
   `$isArray`/`$cond` and add coverage.
   **OPEN.** Reproduced — see Finding 2.

Two `CHANGES_REQUESTED` reviews from `Fabdulla1` (2026-07-22 and
2026-07-29) are still outstanding and block merge.

## Checks and qlty

All 13 check runs pass; the two `docker` runs are `skipped`. CodeQL,
GitGuardian (both the action and the app), Sourcery review,
`Analyze (python)`, and `Test Python 3.11 / 3.12 / pypy-3.11` are all
`success`.

Commit statuses `qlty check`, `qlty coverage`, and `qlty coverage diff`
are all `success`, and the combined status is `success`. **There are no
failing checks and no reported qlty issues.** The qlty issue detail page
requires sign-in, so the green status is the available evidence; qlty left
no annotations or comments on the PR. A local `qlty check` is not
possible — the repo has no tracked `qlty.toml`, so the CLI reports the
repository is not set up.

## Findings

### Finding 1 — `/realia/ids` shadows the entry whose `_id` is `ids`

**Severity: High.** Reviewer comment 4, unaddressed.

`api.add_route("/realia/ids", ...)` is registered alongside
`/realia/{realia_id}`. Falcon gives the static segment precedence, so an
entry with `_id == "ids"` becomes unreachable. The problem is worse than
the `"all"` case it replaced, because the new endpoint **lists that very
ID in its own response**: a sitemap built from `/realia/ids` will contain
a URL the API cannot serve. The documented fallback does not help —
`realiaId` defaults to `""` in `RealiaEntrySchema`, and
`/realia/by-id/ids` returns 404.

There is a test asserting `"all"` is reachable, but **no test asserts
anything about `"ids"`** — the exact collision the reviewer raised.
Coverage is 100% by line, but this behaviour is untested.

Options, in my order of preference:

1. Move the listing off the entry namespace entirely, e.g. `/realia-ids`
   or `/realia/-/ids`, so no raw `_id` can ever collide. This is the only
   option that closes the class of bug rather than one instance.
2. Reserve `"ids"` (and `"all"`) as identifiers across every creation and
   import path, and add a test that the reservation holds.
3. Accept and document the constraint — but then the listing must at
   least exclude the shadowed ID from its own output, so consumers are
   not handed an unusable URL.

### Finding 2 — one malformed legacy document 500s `/realia/ids`

**Severity: High.** Reviewer comment 5, unaddressed. Confirmed against a
running instance.

`_array_size` is `{"$size": {"$ifNull": [f"${field}", []]}}`. `$ifNull`
only substitutes for missing/null; it does not coerce a scalar or object.
When `$size` receives a non-array MongoDB raises `OperationFailure`, which
aborts the whole query — so a **single** malformed document takes down the
endpoint for every consumer, and with it sitemap generation.

The bug is masked in casual testing because `$and` and `$or`
short-circuit: a document is only at risk once it is redirect-shaped
(`crossReferences` holding exactly one entry), which is when the
own-content branch actually evaluates. `crossReferences` itself is
unguarded too and fails immediately regardless of shape.

Measured on a local instance (`mongod` at 127.0.0.1:27017, this branch's
code):

- redirect-shaped + `type: "Divine names"` → `OperationFailure: The
  argument to $size must be an array, but was of type: string`
- redirect-shaped + `wikidataId: "Q787"` → same error
- redirect-shaped + `reallexikon: {…}` (object) → `OperationFailure:
  input to $filter must be an array not object`
- `crossReferences` an object → `The argument to $size must be an array,
  but was of type: object`
- `crossReferences` a scalar string → same error
- non-redirect-shaped + `type: "Divine names"` → listed; it
  short-circuits before `$size`, so it silently survives
- one malformed document, over HTTP → `GET /realia/ids` returns **500**,
  while `GET /realia/Anu` still returns 200

The inconsistency is notable: `_is_resolvable_reference` already does
exactly the right thing, switching on `{"$type": …}` and defaulting to
`False`. The array fields deserve the same treatment.

Recommended fix — coerce defensively in `_array_size`, mirroring the
`$switch` discipline already used for references:

```python
def _array_size(field: str) -> dict:
    value = f"${field}"
    return {"$size": {"$cond": [{"$isArray": value}, value, []]}}
```

and apply the same `$isArray` guard to the `$filter` input in
`_resolvable_reallexikon_count`. Add repository tests for each malformed
shape listed above — the reviewer explicitly asked for that coverage.

I have not checked production data for these shapes, because `.env`
`MONGODB_URI` points at the live cluster. Whether malformed documents
exist today should be confirmed before deciding this is theoretical; note
that the endpoint's blast radius is total (500 for everyone), not
per-document.

### Finding 3 — three unrelated tooling files conflict with master

**Severity: High (blocks merge), trivial to fix.**

The PR is `CONFLICTING`. All three conflicts are in files unrelated to the
feature: `.github/instructions/copilot.instructions.md`, `.gitignore`, and
`Taskfile.dist.yml`. Master already carries equivalent-or-better versions
of every one of these changes:

- **`copilot.instructions.md`** — the branch appends `task type` and
  `task type-pyright` as gates 6 and 7. Master already lists them as gates
  3 and 4 in a reordered 8-gate list, with a fuller three-type-checker
  section. The branch version is an earlier draft.
- **`Taskfile.dist.yml`** — both add a `type-pyright` task. Master's
  version is more robust: it falls back from `origin/master` to `master`
  and pipes through `xargs`.
- **`.gitignore`** — master already ignores `.claude/` and `.qlty/`. The
  branch differs only by adding `CLAUDE.md` / `CLAUDE.local.md` and using
  `# Qlty` instead of `# qlty` as the comment.

Recommendation: drop all three files from this PR (take master's side
wholesale). That resolves every conflict and removes unrelated scope. If
ignoring `CLAUDE.md` / `CLAUDE.local.md` is still wanted, it belongs in
its own one-line PR.

### Finding 4 — title and description describe the superseded design

**Severity: Medium.**

The title still reads "Add GET /realia/all endpoint for listing Realia
IDs" and the body says the endpoint "returns a JSON array of all Realia
`_id`s" and describes `GET /realia/all`. Neither is true: the route is
`/realia/ids`, and it deliberately returns a *filtered* subset, excluding
bare redirect stubs. The Sourcery-generated summary in the body is stale
for the same reason. Since the stated purpose is sitemap generation, the
exclusion rule is exactly the part a future reader most needs documented.

### Finding 5 — the stub rule treats 0 and 2+ cross-references as content

**Severity: Medium — needs a domain decision, not necessarily a code
change.**

`REDIRECT_CROSS_REFERENCE_COUNT = 1` means only an entry with *exactly
one* cross-reference and no own content is filtered out.
`test_list_non_redirect_ids_lists_entry_with_several_cross_references`
codifies that an entry with two cross-references and nothing else **is**
listed. A two-target disambiguation entry with no own content has just as
little to render as a one-target redirect, so it will produce a sitemap
URL pointing at an empty page.

Please confirm with the domain owner that this is intended. If it is, the
constant name should say so — `REDIRECT_CROSS_REFERENCE_COUNT` reads like
a tunable, not a deliberate exactly-one rule — and the reasoning belongs
in the PR description.

### Finding 6 — `$expr` on every request cannot use an index

**Severity: Low.**

`non_redirect_stub_query` is a pure `$expr` filter, so MongoDB cannot use
an index for it; every uncached request is a full collection scan that
evaluates a nested expression per document, then sorts the full result set
in Python. `Cache-Control: public, max-age=600` protects downstream
consumers, but there is no server-side caching, so any cache miss or
direct call pays full cost, and the response is unbounded.

At current Realia volumes this is almost certainly fine, and I would not
block on it. Worth a comment recording the choice, and worth revisiting if
the collection grows or the endpoint is called more often than the sitemap
job.

### Finding 7 — `realia_id` names two different id types

**Severity: Low. Pre-existing, but this PR adds a third route to the
space.**

`/realia/{realia_id}` resolves against `_id`, while
`/realia/by-id/{realia_id}` resolves against `realiaId` — two distinct
identifier namespaces sharing one parameter name. The type of the value is
not knowable from where it sits, which is the same failure mode the
project's data hard gate exists to prevent (stated there for arrays; the
principle is identical here). It also directly weakens the fallback in
Finding 1: at a glance `/realia/by-id/ids` looks like it should work.

A rename such as `/realia/{entry_id}` versus `/realia/by-id/{realia_id}`
would make the distinction self-evident. Out of scope for this PR, but
worth an issue.

### Finding 8 — minor cleanups

**Severity: Low.**

- `IF_NULL = "$ifNull"` (`realia_stub_filter.py:4`) adds a layer of
  indirection over a MongoDB operator literal while `$size`, `$filter`,
  `$switch` and the rest stay inline. It reads as inconsistent; inline it.
- `query = req.get_param("query", default="") or ""` (`realia.py:47`) —
  with `default=""` Falcon never returns `None` here, so the `or ""` is
  unreachable. It is an unrelated drive-by in a search resource this
  feature does not touch.
- The `cast(...)` additions in `_load_entry` and `search` are likewise
  unrelated to the feature. They are harmless and satisfy the type
  checkers, but they widen the diff.

## Data hard-gate check

No violation in the new code. `/realia/ids` returns a single array holding
exactly one type of value (Realia `_id` strings) — no mixed id list, no
discriminator, no probing, and no domain/wire shape mismatch.
`RealiaEntry` keeps `id` and `realia_id` as separate fields rather than
one field carrying either. Finding 7 is the adjacent concern, at the route
layer rather than in an array.

## Reproduction steps

All reproduced on this branch at `924340f0` against a real local MongoDB
(`127.0.0.1:27017`), with the service run from this tree. `task start` was
deliberately **not** used, because `Taskfile.dist.yml` declares
`dotenv: [".env"]` and `.env` `MONGODB_URI` points at the production
cluster.

### Finding 1 — route shadowing

1. Seed a local database with realia documents including `_id: "ids"` and
   `_id: "all"`.
2. Serve `ebl.app.create_app(ebl.app.create_context())` with
   `MONGODB_URI=mongodb://127.0.0.1:27017` on port 8123.
3. `curl http://127.0.0.1:8123/realia/ids` returns `200` and a body that
   includes `"ids"`:
   `["(Heiliger) Hügel", "Ähre", "all", "Anu", "Enlil, Ellil", "ids",
   "Pig"]`
4. `curl http://127.0.0.1:8123/realia/all` returns `200` and the entry —
   the old collision is fixed.
5. `curl http://127.0.0.1:8123/realia/ids` again — still the list, never
   the entry. The entry is unreachable.
6. `curl http://127.0.0.1:8123/realia/by-id/ids` returns `404`:
   `"Realia entry with realiaId 'ids' not found."`

### Finding 2 — 500 from one malformed document

1. With the service from step 2 above running, insert:

   ```python
   collection.insert_one({
       "_id": "Legacy-Scalar",
       "crossReferences": [{"id": "Canonical", "lemma": "Canonical"}],
       "type": "Divine names",
   })
   ```

2. `curl http://127.0.0.1:8123/realia/ids` returns **`500`**:
   `{"title": "500 Internal Server Error"}`
3. `curl http://127.0.0.1:8123/realia/Anu` returns `200` — only the new
   endpoint is broken.
4. The `crossReferences: [...]` wrapper matters: without it the `$and`
   short-circuits before `$size` evaluates, and the malformed document is
   silently listed instead of raising.

### Finding 3 — conflicts

```bash
git merge-tree --write-tree --name-only HEAD origin/master
# CONFLICT (content): .github/instructions/copilot.instructions.md
# CONFLICT (content): .gitignore
# CONFLICT (content): Taskfile.dist.yml
```

## Gates run for this review

- `task format` — exit 0, 733 files already formatted.
- `task lint` (ruff) — exit 0, all checks passed.
- `task type` (pyre) — exit 0, "No type errors found".
- `task type-pyright` — 0 errors, 0 warnings, 0 informations.
- `mypy` on the 8 changed modules — 0 errors in the changed files.
- `flake8 --max-line-length=120` on the 8 changed modules — exit 0.
- `pytest ebl/tests/realia --cov=ebl/realia` — 91 passed, **100%**
  coverage, 0 missing lines.
- 250-line file limit — pass; the largest changed file is
  `mongo_realia_repository.py` at 157 lines.
- `task lint-md` — clean.
- Running-service verification — performed, see Reproduction Steps.

## Recommendation

**Request changes.** Do not merge yet.

Blocking:

1. **Finding 2** — guard the array expressions with `$isArray`/`$cond`
   and add the malformed-shape coverage the reviewer asked for. A single
   bad document currently 500s the endpoint.
2. **Finding 1** — resolve the `"ids"` collision, ideally by moving the
   listing out of the entry namespace, and add a test for it. At minimum,
   stop listing an ID the API cannot serve.
3. **Finding 3** — drop the three unrelated tooling files and take
   master's versions; this clears all three merge conflicts.
4. **Finding 4** — update the PR title and description to describe
   `/realia/ids` and the redirect-stub exclusion.

Non-blocking: confirm the domain rule in Finding 5, and take the cleanups
in Findings 6–8 as convenient. Finding 7 is worth its own issue.

Once Findings 1–4 are done this is a clean, well-tested change — the
sorting helper, the cache header, the 100% coverage, and the resolution of
both Sourcery comments are all good work.

## Post-fix addendum

### Critical: the rename would have broken the deployed frontend

`ebl-frontend` master calls `` `/realia/all` `` from
`src/realia/infrastructure/RealiaRepository.ts` (`listAllRealia`), used by
`src/router/sitemap.tsx`. It reached frontend master in PR #762, merged
2026-08-11.

Backend master has **no** realia listing route at all, so that frontend
call currently 404s in production. Had #735 merged as `/realia/ids`, it
would have stayed broken. The endpoint is now `/realia/all` again, matching
the deployed client.

This also reframes Fabdulla1's original comment: the answer to the `"all"`
collision could not be a rename, because the client name was already fixed.

### Finding 9 — the listing could emit an ID whose entry route 500s

**Severity: High. Found during post-fix re-verification; now fixed.**

After the `$isArray` guard stopped the listing from failing, a malformed
document was still *listed* — and `GET /realia/Legacy-Object` returned
`500`, because `RealiaEntrySchema().load()` rejects a non-list value for a
`fields.List`. A sitemap built from the endpoint would contain a URL that
500s.

The entry-route failure is pre-existing (this PR touches `_load_entry`
only to add a `cast`), but the listing turns a latent data defect into a
published broken URL.

Fix: `realia_document_shape.well_formed_arrays_expression()` requires every
known array field to be absent, null, or an actual array. Malformed
documents are excluded from the listing instead of emitted. Verified over
HTTP: every listed ID now returns 200 individually.

### Outstanding decisions

1. **Finding 5** — is "exactly one cross-reference and no own content" the
   right definition of a redirect stub, or should any entry with
   cross-references and no own content be excluded? Behaviour is unchanged
   pending this answer.
2. **Finding 4** — the PR title and body still describe `/realia/all`
   returning *all* IDs. They now need to describe the redirect-stub,
   reserved-identifier, and malformed-document exclusions. Awaiting
   authorisation to edit the PR.
3. **Test removal** — `test_entry_named_all_is_reachable` asserted that
   `GET /realia/all` returns the entry whose `_id` is `"all"`. That is
   false by design now that `/realia/all` is the listing route. It was
   replaced by `test_list_excludes_reserved_identifiers` and
   `test_every_listed_id_is_retrievable`. Per project rules this removal
   needs explicit approval.
4. **Tooling regression from Finding 3** — master's `type-pyright` task
   reads the committed diff only, ignores explicit paths, and skips
   untracked files, so it cannot check a tree containing an uncommitted
   rename. The branch's version handled both. Worth a separate PR against
   master; pyright was run directly here instead.

## Note before merge

`TASK-735-todo.md`, `TASK-735-log.md`, `TASK-735-review.md`,
`TASK-735-fix-todo.md`, and `TASK-735-fix-log.md` are task tracking
artifacts and **must be removed before this PR is merged**.
