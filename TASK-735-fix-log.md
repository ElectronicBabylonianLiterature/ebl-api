# TASK-735-fix Work Log — Address review findings on PR #735

Task: address every finding recorded in `TASK-735-review.md`.

New task, so new tracking files — the previous task's `TASK-735-todo.md`
and `TASK-735-log.md` cover the review and do not carry forward.

## Entries

### 1. Task start

- Created `TASK-735-fix-todo.md` and this log before making any change.
- Read `ebl/realia/web/bootstrap.py` in full first. It registers a sink,
  `api.add_sink(realia_lemma_sink, prefix=r"/realia/(?P<realia_id>.+)")`,
  which catches every unmatched path under `/realia/`. Any fix for
  Finding 1 must sit outside that prefix to be genuinely collision-free.
- Surveyed existing route conventions: the codebase uses `/{resource}/all`
  (`/bibliography/all`, `/signs/all`, `/words/all`, `/corpus/texts/all`).
  Those carry the same latent collision, but their identifier spaces
  (ObjectIds, sign names) make it far less likely than realia `_id`s,
  which are arbitrary lemma strings.

### 2. User decision: use the route ebl-frontend already calls

- Asked which route name to use; the user answered "pick the one that is
  used in ebl-frontend". No local frontend checkout exists, so queried
  GitHub.
- `ebl-frontend` master, `src/realia/infrastructure/RealiaRepository.ts`:
  `listAllRealia()` calls `` `/realia/all` ``. Called from
  `src/router/sitemap.tsx` via `RealiaService`. Six files reference it.
- That call reached frontend **master** in PR #762 "Add Realia entries to
  sitemap via slugs", merged 2026-08-11.
- Timeline that explains the mismatch:
  - 2026-07-03 backend #735 adds `/realia/all` (commit `f8e6c9e6`).
  - 2026-07-28 backend renames it to `/realia/ids` (commit `8b7f4632`)
    to answer Fabdulla1's shadowing comment.
  - 2026-08-11 frontend #762 merges calling `/realia/all` — written
    against the original design, not the rename.
- **Backend master has no listing route at all** (verified:
  `git show origin/master:ebl/realia/web/bootstrap.py`), so the frontend
  sitemap call currently 404s in production, and merging #735 as
  `/realia/ids` would leave it broken permanently.
- Decision: restore `/realia/all` as the route. Finding 1's collision
  must therefore be solved without renaming.

### 3. Revised approach to Finding 1

Renaming is off the table, so the collision is addressed structurally
instead:

- Single source of truth for the reserved identifier in the domain layer,
  so the route registration and the listing query cannot drift apart.
- The listing excludes reserved identifiers, so a sitemap built from the
  endpoint can never contain a URL that resolves to the listing itself.
- Tests assert both the exclusion and that every listed ID is retrievable.

### 4. Changes made

- Finding 3: restored master's versions of
  `.github/instructions/copilot.instructions.md`, `.gitignore` and
  `Taskfile.dist.yml` with `git checkout origin/master -- <paths>`;
  verified all three now match master byte for byte.
- Finding 1: added `ebl/realia/domain/reserved_identifiers.py` holding
  `LIST_ROUTE_SEGMENT = "all"` and `RESERVED_REALIA_IDS`. `bootstrap.py`
  builds the route from that constant and the repository excludes those
  ids with `{"_id": {"$nin": ...}}`, so route and query cannot drift.
- Finding 1: route restored to `/realia/all` to match ebl-frontend.
- Finding 2: replaced `$ifNull` coercion with an `$isArray`/`$cond`
  guard (`_as_array`), applied to every `$size` and to the `$filter`
  input. This removed the `IF_NULL` constant, which also settled the
  first item of Finding 8.
- Finding 5: renamed `REDIRECT_CROSS_REFERENCE_COUNT` to
  `EXACTLY_ONE_CROSS_REFERENCE` so the constant states the rule.
  Behaviour deliberately unchanged — the rule itself still needs a
  domain decision.
- Finding 7: `/realia/{realia_id}` and the sink now use `entry_id`,
  distinguishing the `_id` namespace from `realiaId`. URLs unchanged.
- Tests: renamed `test_realia_ids_route.py` to
  `test_realia_list_route.py`; added
  `test_realia_stub_filter_robustness.py`; added reserved-identifier
  coverage to `test_realia_list_ids.py`.

### 5. Finding 8: two of three suggestions were wrong

I proposed removing the `or ""` and the two `cast(...)` calls as
unrelated noise. I tested that before acting: removing them produces
**5 pyright errors** (`reportArgumentType`, `reportReturnType` —
marshmallow `load()` is untyped). They are load-bearing under the
three-checker gate, so I restored them. Only the `IF_NULL` inlining was
correct. My review was wrong on this point.

### 6. Mistake: stale verification output nearly reported

The first re-verification run after the rewrite printed a `/realia/all`
body that looked correct, but the server had failed to start and `curl`
had left the previous run's `/tmp/b.json` in place — every follow-up
request returned HTTP 000. I caught it because the status codes were
000, deleted the stale file, restarted the service properly, and re-ran
everything. Nothing from that void run was used.

### 7. New issue found during re-verification, and fixed

With the `$isArray` guard in place the listing no longer 500s, but a
malformed document (`crossReferences` as an object) was still *listed*,
and `GET /realia/Legacy-Object` returned **500** — because
`RealiaEntrySchema().load()` rejects a non-list for a `fields.List`.
So the endpoint would hand the sitemap a URL that 500s, breaking the
very invariant my new test asserts.

Confirmed pre-existing: this PR changes `_load_entry` only by adding a
`cast`, so the entry-route failure exists on master too. But the listing
turns a latent data defect into a broken sitemap URL.

Fix: added `ebl/realia/infrastructure/realia_document_shape.py` with
`well_formed_arrays_expression()`, requiring every known array field to
be absent, null, or a real array. `non_redirect_stub_query()` became
`non_redirect_stub_expression()` so the repository can `$and` the two
expressions under one `$expr`. Malformed documents are now excluded from
the listing rather than emitted. The `_as_array` guards are kept as
defence in depth — relying on `$and` short-circuiting is what hid the
original bug.

### 8. Verification against the running service (final code)

Service rebuilt from the final tree, local mongo, port 8124, seeded with
well-formed entries plus `all`, `ids`, a redirect stub, and three
malformed legacy documents:

- `GET /realia/all` → 200,
  `["(Heiliger) Hügel", "Ähre", "Anu", "Enlil, Ellil", "ids", "Pig"]`,
  `Cache-Control: public, max-age=600`.
- Every listed id fetched back individually → **all 200**. The
  "every listed ID is retrievable" invariant holds against real HTTP.
- `all`, `Legacy-Object`, `Legacy-Scalar`, `Legacy-Reallex` and
  `Redirect-Stub` are all present in the database and all correctly
  absent from the listing. No 500 anywhere.
- `GET /realia/ids` now returns the ordinary entry — the shadowing
  introduced by the rename is gone.
