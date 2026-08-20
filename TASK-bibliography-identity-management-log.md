# Work Log: Bibliography Trusted Identity Management

## Phase 0 — Branch preparation

- Read `.github/instructions/copilot.instructions.md`. No `CLAUDE.md`,
  `AGENTS.md`, or `.github/copilot-instructions.md` present; the
  `.github/instructions/` file is the sole instruction source.
- Starting state: on `fix-bib` at `513ae34a`, `master` == `origin/master` ==
  `a106548a`. Working tree had no tracked modifications, only pre-existing
  untracked files (MAP_*, TASK-m2m-*, docs/*, archives). None touched.
- Requested branch `bibliography-identity-managment` did not exist. `git fetch`
  revealed the real remote branch `bibliography-identity-management` (correct
  spelling). Recorded as a typo in the request, not a missing branch.
- `origin/bibliography-identity-management` == `a106548a` == `origin/master`:
  an untouched branch, already current with master. No update needed for that.
- Verified master lacks PR #752: `server_owned_fields.py`,
  `redirect_resolution.py`, `bibliography_queries.py` exist only on `fix-bib`.
- `git merge-base fix-bib origin/master` == `2169b155`. Master carries one
  commit `fix-bib` lacks (`a106548a`, security bumps); `fix-bib` carries seven.
- ERROR AVOIDED: the request said both "incorporate that branch cleanly" (§2)
  and "do not merge" (§21), and the repo hard-gates `git merge`. Did not guess.
  Asked the user, who chose merging `fix-bib`.
- `git merge fix-bib --no-edit` -> `d0d0d86f`. Clean, no conflicts, no
  force-push. Branch is now `master + #752`.

## Phase 1 — Investigation findings

- `update_with_identity_claims` diffs `identity_values(old)` vs
  `identity_values(new)`, claims added values, persists, commits, retires
  removed values, then writes the changelog. Rollback releases pending claims
  only when persistence has not happened.
- CAS already exists: `repository.update(entry, expected_server_owned_fields)`
  filters on the server-owned state read at load time
  (`server_owned_state_filter`), raising `BibliographyUpdateConflictError`
  (a `DuplicateError` -> HTTP 409) when another operation moved it.
- Legacy records without reservations are already handled:
  `MongoLookupReservations.retire` suppresses `NotFoundError`, so retiring an
  unreserved value is a no-op, and `ensure_lookup_values_available` checks the
  bibliography collection through `Bibliography.find`, not the reservation
  collection, so an unreserved legacy alias still blocks a colliding claim.
- Redirect policy lives in `follow_bibliography_redirect`, `MAX_REDIRECT_DEPTH`
  = 5. It raises `NotFoundError` for a missing target and `DuplicateError` for
  loops and depth violations.
- Error mapping: `NotFoundError` -> 404, `DuplicateError` -> 409,
  `DataError` -> 422, jsonschema violation -> 400.
- AUTHORIZATION — the important finding. `ebl/app.py` mounts internal
  `/bibliography/*` and partner `/api/v1/bibliography/*` on the SAME falcon
  app, behind the SAME `Auth0Backend`. M2M partner clients are distinguished
  only by `gty == "client-credentials"` for the profile factory; nothing
  separates the surfaces. `write:bibliography` is required by BOTH the internal
  update route and the partner write routes. Guarding the new route with
  `write:bibliography` would therefore hand it to every partner M2M client.
  There is no existing curator-only bibliography write privilege
  (`check:bibliography_duplicates` is a read/check scope,
  `export:bibliography` is partner read). One new restricted enum member is
  the minimal correct answer.

## Phase 2 — Design decisions

- Contract: EXPLICIT COMMANDS, not full intended state. Full-state alias
  replacement makes accidental removal a single omitted array element, and
  under concurrency it erases a concurrent addition instead of conflicting.
  Explicit commands make removal deliberate and, combined with the existing
  CAS, turn a concurrent alias addition into a 409 rather than a silent loss.
- Tombstones are expressed as `deprecateTo` / `reactivate`, never as raw
  `deprecated` / `redirectTo`. This makes an invalid tombstone structurally
  unrepresentable: `deprecated` without a target cannot be requested at all.
  The two are mutually exclusive in the schema.
- Redirect validation reuses `follow_bibliography_redirect` against the
  prospective entry rather than reimplementing depth/cycle rules, so there can
  be no second conflicting policy. Its `NotFoundError`/`DuplicateError` are
  converted to `DataError` (422) because the submitted request is what is
  invalid, not the addressed record.
- Route `POST /bibliography/{id_}/identity`. POST because the repo has no
  `on_patch` anywhere; every write is POST.
- Scope `admin:bibliography` (RESTRICTED), new enum member.
- File-size pressure drove the module split: `bibliography_entry.py` is at
  exactly 250 lines and `bibliography.py` at 242, so the schema, the state
  transformation, the validation, the service and the resource each get their
  own module and `Bibliography` is not modified at all.

## Phase 3 — Implementation

Six production files: one new scope enum member, one request schema, one pure
state transformer, one validator, one application service, one web resource,
plus route registration. `Bibliography` itself was not touched.

## Phase 4 — Tests

Eleven new test modules, 92 new tests. Two assertion errors of my own, both
found by running the tests, both my test being wrong rather than the code:

1. `test_conflict_leaves_no_reservation_or_changelog_trace` asserted the loser's
   reservation would be `abandoned`. It is actually deleted: the CAS conflict
   fires inside `repository.update`, so `updated` is still False and
   `release_pending_lookup_values` removes the pending row outright. The real
   behaviour is stronger than what I asserted; the assertion was corrected to
   expect no row at all.
2. Ruff B017 flagged `pytest.raises(Exception)` in the recovery suite. Narrowed
   to `pytest.raises(DataError, match="cannot redirect to itself")`.

## Phase 5 — Quality gates

- ERROR MADE AND RECOVERED: `task type-pyright` reported 0 errors, but its
  `git diff origin/master...HEAD` file list only covers COMMITTED files, and
  every new file here is uncommitted. Running pyright directly on the new files
  exposed 108 real errors. All were test-side indexing of `result.json` and
  `find_one`, which pyright types as a JSON union / Optional. Fixed centrally by
  adding typed `body`, `description`, `stored` and `reservation` helpers that
  narrow with `cast`, then updating call sites. Pyright now reports 0 errors on
  the new files. Do not trust `task type-pyright` for uncommitted work.
- ruff check / ruff format / flake8 / git diff --check: clean.
- pyre: 6 errors, all in pre-existing untracked `docs/handoffs/**/scripts/*.py`
  (`import dbconn`), present before this task and untouched by it. Zero in `ebl/`.
- mypy: zero errors in the changed files. The 61 it reports are in unrelated
  modules it pulls in through imports.
- Coverage: 100% on all six new/changed production modules.
- Full suite NOT run: the user instructed mid-task not to. Ran
  `ebl/tests/bibliography ebl/tests/common ebl/tests/users
  ebl/tests/fragmentarium/test_fragment_scope.py` instead (776 passed) to cover
  the shared `scopes.py` change.
- File-size gate: largest new file is 162 lines, all under 250.
- markdownlint on the two task files: 0 errors.

## Phase 6 — Runtime verification

Served the real app with waitress on 127.0.0.1:8123 and issued real HTTP
requests (scratchpad script, not added to the repo):

    add alias + citationKey  -> 200
    GET by the new alias     -> 200, resolves to Q40000001
    colliding alias          -> 409
    self redirect            -> 422
    deprecate                -> 200
    GET follows the redirect -> 200, resolves to Q40000002
    raw `deprecated` field   -> 400
    partner M2M scopes       -> 403

## Git state

Merge commit `d0d0d86f` exists (user-authorized). The implementation itself is
staged but NOT committed, per the user's instruction to `git add` only.
