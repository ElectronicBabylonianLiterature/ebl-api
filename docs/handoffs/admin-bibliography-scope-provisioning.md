# Provisioning `admin:bibliography`

`POST /bibliography/{id}/identity` — the only route that can add or remove an
alias, set or clear a `citationKey`, deprecate an entry, or reactivate one —
is guarded by the scope `admin:bibliography` (`ebl/common/domain/scopes.py`).

**As of this handoff, no Auth0 role, API permission, or M2M client in this
repository's tracked configuration grants that scope.** It is not listed in
this README's Scopes section prior to this change, nor in
`M2M_Auth0_instructions.md` / `M2M_Auth0_manual.md`. Auth0 itself is
configured outside this repository, so nothing here can confirm or change
what is actually provisioned in the live tenant — treat the scope as
unprovisioned until someone with Auth0 access confirms otherwise.

## Why this was tracked as a blocker before provisioning

Several defects that made early provisioning unsafe were found and fixed on
this branch:

- a legacy identity value (no reservation row — true of all pre-migration
  data) could be claimed a second time by the entry its own tombstone
  redirects to, silently duplicating a citation key or alias onto two
  documents (fixed: literal, non-redirect-following lookup ownership check);
- the identity operation could silently revert a concurrent, unrelated
  metadata edit, with no error and no changelog trace (fixed: identity writes
  now touch only the four identity fields, never the rest of the document);
- deprecating an entry could push an *existing* tombstone that already
  redirected to it past the maximum redirect depth, invisibly, because
  validation only walked forward from the entry being changed (fixed:
  inbound chains are now walked and re-validated too);
- two reconcilers racing the same stale/committed lookup reservation could
  raise an uncaught `NotFoundError` from an operation that never touched the
  contested value, since `reconcile_lookup_reservations` runs unconditionally
  at the start of every claim (fixed: the reconciliation transition is now
  idempotent against a concurrent reconciler that already made the same
  transition, mirroring the existing `retire`/`release_pending` pattern).

None of these were reachable in production before now, because nothing
granted the scope. They are fixed as of this branch, so that is no longer a
reason to withhold provisioning.

## Known limitation: concurrent cross-record redirects (single-writer constraint)

Per-record compare-and-set correctly serializes two identity operations on
the *same* record, but it cannot serialize two identity operations on
*different* records. Two concurrent requests can each validate against the
other record's current, not-yet-changed state and both pass their own CAS.
Two shapes are reachable:

- a **two-record cycle** — one request sets `A.redirectTo = B` while the
  other sets `B.redirectTo = A`;
- an **over-depth chain** — two curators extend redirect chains that share a
  downstream node, pushing an inbound predecessor past
  `MAX_REDIRECT_DEPTH`; no mutual redirect is required.

Either shape makes the affected records unresolvable: a direct read returns
`409` (`GET /bibliography/{id}`), a `GET /bibliography/list` batch that
includes an affected id now silently drops that id rather than failing the
whole batch, and corpus / fragment reference resolution
(`Bibliography.find_many`, `Bibliography.canonicalize_references`) skips the
unresolvable reference instead of raising.

**Mitigation on this branch (narrows, does not close, the window):** after a
successful identity write, `BibliographyIdentityManagement` re-resolves the
changed entry and its inbound chains; if the concurrent change broke
resolution, it rolls the write back (an identity-only compare-and-set
restore) and returns `409`. Every interleaving now converges to a consistent
state — the second request to reach the post-write re-check loses. A genuine
double-persist-before-either-re-check remains theoretically possible.
Regression coverage:
`test_bibliography_identity_management_concurrency.py::test_a_concurrent_cross_record_redirect_break_is_rolled_back`.

**Operational consequence: until a transaction or lock spans both records,
`admin:bibliography` should still be treated as a single-writer curator
capability** — granted to one trusted operator/process at a time. Follow-up:
open an issue for cross-record redirect serialization (MongoDB multi-document
transaction around validate + persist for `deprecateTo`) before the scope is
granted to more than one writer.

## Still worth doing first, not a hard blocker

`bibliography_lookup_reservations` holds no rows for pre-migration identity
data (see the `alias-bib-id` / identity-merge handoff notes). The literal
lookup ownership fix above means correctness no longer depends on that
backfill running — the check now looks at the `bibliography` collection
directly rather than trusting the reservation collection to be complete.
Running the backfill is still recommended before heavy use of the identity
route, so that lookup-value claims resolve through the fast, indexed
reservation path instead of the collection scan behind
`ensure_lookup_values_available`'s fallback.

## Provisioning steps (Auth0, external to this repository)

1. In the Auth0 API used by this application, add the permission
   `admin:bibliography` if it does not already exist.
2. Grant it only to the trusted internal operator role/account used by the
   curator identity-management tooling. **Do not** grant it to any M2M
   client used by a partner integration — internal and partner routes share
   one app and one auth backend (see
   `ebl/bibliography/web/bibliography_identity_management.py`'s module
   docstring), so a partner client holding this scope would reach the
   identity route directly. Keep this to a single trusted operator/process at
   a time per the single-writer constraint above, until cross-record
   redirect serialization exists.
3. Confirm the grant by requesting a token for that role/account and
   checking its `scope` claim or `permissions` array includes
   `admin:bibliography` (`ebl/users/infrastructure/auth0.py` reads both).
4. Smoke-test against a non-production environment: `POST
   /bibliography/{id}/identity` with a trivial command (e.g. add and then
   remove a throwaway alias) and confirm `200`, then confirm a request from a
   credential that lacks the scope gets `403`.
5. Update this repository's README Scopes section and
   `M2M_Auth0_instructions.md` (if it tracks provisioned scopes for the
   environment being provisioned) once the grant is live, so the tracked
   documentation matches reality.
