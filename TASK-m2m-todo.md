# TASK-m2m-todo.md

## Task: Add M2M Auth0 support for client credentials flow

### Code

- [x] Remove `"openid"` from `required_claims` in `Auth0Backend`
- [x] Add `"sub"` to `required_claims` in `Auth0Backend`
- [x] Add explicit `sub` guard in `authenticate()` raising `HTTPUnauthorized` if absent
- [x] Detect M2M tokens via `gty == "client-credentials"` and skip `/userinfo`
- [x] Set profile name from `sub` for M2M tokens
- [x] Remove `"openid": True` from `create_token()` test helper
- [x] Add `test_auth_backend_m2m_token` — HTTP 200 acceptance test
- [x] Add `test_auth_backend_m2m_token_profile` — asserts profile is `{"name": sub}`, `fetch_user_profile` not called
- [x] Add `test_auth_backend_non_m2m_profile_calls_userinfo` — asserts `/userinfo` is called for regular tokens
- [x] Add `test_auth_backend_missing_sub_is_unauthorized` — missing `sub` returns HTTP 401
- [x] Achieve 100% coverage on `ebl/users/infrastructure/auth0.py`

### Documentation

- [x] Add `M2M_Auth0_instructions.md` — full runbook
- [x] Add `M2M_Auth0_manual.md` — operator manual
- [x] Fix Step N5 branch reference (`add-realia` → `m2m-changes`)
- [x] Update manual: store secrets in `.env`, document sensitivity
- [x] Update all token file paths to use `/tmp` (Finding 3, 11)
- [x] Fix manual Section 7 step caption off-by-one (Finding 9)
- [x] Fix instructions "Dictionary" label to include audience identifier (Finding 8)
- [x] Fix instructions minimal script to use env-var guards instead of inline literals (Finding 10)

### Review

- [x] Create `TASK-m2m-review.md` with initial findings
- [x] Integrate GitHub PR #721 reviews (Sourcery AI + Copilot)
- [x] Mark resolved findings in review file

### Cleanup (before merge)

- [ ] Remove `TASK-m2m-todo.md`
- [ ] Remove `TASK-m2m-log.md`
- [ ] Remove `TASK-m2m-review.md`
