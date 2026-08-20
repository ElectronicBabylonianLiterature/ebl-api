# TASK: Bibliography Trusted Identity Management

Branch: `bibliography-identity-management`

## Phase 0 — Branch preparation

- [x] Read `.github/instructions/copilot.instructions.md`
- [x] Record starting git state
- [x] Locate target branch (remote spelling `bibliography-identity-management`)
- [x] Confirm branch was untouched at `origin/master`
- [x] Confirm `master` lacks PR #752
- [x] Obtain explicit user authorization for the merge
- [x] Merge `fix-bib` (#752) into the branch
- [x] Create TODO and log files

## Phase 1 — Investigation

- [x] Identity primitive `update_with_identity_claims`
- [x] Lookup reservation infrastructure
- [x] Redirect resolution rules and depth limit
- [x] Changelog behaviour
- [x] Authorization model, internal vs partner surface
- [x] Existing identity tests

## Phase 2 — Design

- [x] Choose request contract (full state vs explicit commands)
- [x] Choose route and method
- [x] Choose authorization scope
- [x] Decide module split to respect the 250-line file limit

## Phase 3 — Implementation

- [x] Identity request domain model
- [x] Redirect/tombstone validation before write
- [x] Application service
- [x] Wire to `update_with_identity_claims`
- [x] Web resource
- [x] Route registration

## Phase 4 — Tests

- [x] Alias add / multi-add / remove / replace
- [x] Alias collisions (normalized, canonical id, citationKey, other alias)
- [x] Reservation claimed / retired
- [x] Legacy record without reservations
- [x] citationKey set / replace / remove / conflict
- [x] Tombstone: valid, self, missing, 2-cycle, n-cycle, depth, valid chain
- [x] Reactivation / repair
- [x] Canonical id immutability
- [x] Concurrency / CAS -> 409
- [x] Authorization: trusted ok, unauthorized fails, partner cannot reach
- [x] Compatibility: metadata update still identity-only-preserving
- [x] Failure recovery wired to the service

## Phase 5 — Quality gates

- [x] `poetry run pytest ebl/tests/bibliography`
- [~] full suite - NOT RUN (user instructed not to); ran bibliography +
      common + users + fragment scope instead (776 passed)
- [x] coverage 100% on changed files
- [x] `task type` (pyre)
- [x] `task type-pyright`
- [x] `poetry run ruff check ebl`
- [x] `poetry run ruff format --check ebl`
- [x] `poetry run flake8` changed modules
- [x] `poetry run mypy` changed modules
- [x] `git diff --check`
- [x] 250-line file limit on every changed `.py`

## Phase 6 — Report

- [x] Final report
- [x] Do NOT commit / push / merge / deploy the implementation
