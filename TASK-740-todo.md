# TASK-740 TODO — Review of PR #740 (realiaInfo on fragment routes)

Scope: `f36ed7d9`, the only commit since the previous review (findings
landed in `3b58ebcb`, docs removed in `0a8badca`).

## Review preparation

- [x] Identify review scope (commits since last review)
- [x] Locate PR (#740) and confirm base/head
- [x] MANDATORY: fetch all existing GitHub feedback
  - [x] `gh api .../pulls/740/reviews` — sourcery-ai only, declined (too large)
  - [x] `gh api .../pulls/740/comments` — none
  - [x] `gh api .../issues/740/comments` — none
  - [x] Check merged-in branch PRs — none apply
  - [x] Every finding addressed or acknowledged (no findings to address)

## Analysis

- [x] Read full diff of `f36ed7d9`
- [x] Verify all `create_response_dto` call sites migrated to factory
- [x] Check data hard gate: one array, one type; no probing; no mixed ids
- [x] Check for fragment-returning routes missed by the refactor
- [x] Assess `resolve_realia_info` performance on write routes
- [x] Review `cast()` additions and `req.context` access change

## Gates

- [x] `pytest` (fragmentarium + realia) — 933 passed
- [x] Coverage on changed modules — 100% except `edition.py:58`
- [x] `mypy` changed files — clean (34 errors all in imported modules)
- [x] `flake8 --max-line-length=120` — 2 × E203, pre-existing class
- [x] File length ≤ 250 — 4 changed files over, all over on master already
- [x] `task lint-md` — 0 errors
- [x] Verify by running the modified backend service (not tests alone)

## Deliverables

- [x] `TASK-740-review.md` using the mandated template
- [x] `TASK-740-todo.md` (this file)
- [x] `TASK-740-log.md`
- [x] Remind to remove all TASK-*.md files before merge

## Addressing the findings (user request: all except task docs)

- [ ] 1. Remove committed task docs — EXCLUDED by the user; still a blocker
- [x] 2. `retrieve-all` omits `realiaInfo` — fixed with a batched resolver
  - [x] `resolve_realia_info_for_documents` (one query per page)
  - [x] `_to_realia_info` extracted; single and batched paths share it
  - [x] `realia_repository` injected into `FragmentsRetrieveAllResource`
  - [x] `bootstrap.py` wiring updated
  - [x] Tests: empty case, resolution + single-batched-call, dangling id
  - [x] Verified on the wire (skip=3899, 1000 fragments)
- [x] 3. `edition.py:58` — original recommendation was wrong; the line was
      unreachable dead code. Removed it; module now 100%.
- [x] 4. `task type-pyright` — `master` fallback + `xargs` quoting
- [x] 5. `cast()` proliferation — no change; rationale recorded
- [x] 6. `req.context` inconsistency — no change; rationale recorded
- [x] 7. Scope creep — no change; rationale recorded

## Post-change gates

- [x] `ruff format` / `ruff check` — clean
- [x] Full suite — 3922 passed; 1 pre-existing flake (`sign_images`)
- [x] Coverage on changed modules — 100%
- [x] `mypy` changed files — clean
- [x] `pyright` changed files — 0 errors
- [x] File length ≤ 250 — compliant (`fragments.py` exactly 250)
- [x] `task lint-md` — 0 errors
- [x] Re-ran the modified service and verified finding 2 on the wire

## Reminders

- Two `TASK-realia-fragment-debug-*.md` files are committed in `f36ed7d9`
  and must be removed before merge (review finding 1).
- These three `TASK-740-*.md` files must also be removed before merge.
- Nothing is to be committed unless explicitly requested.
