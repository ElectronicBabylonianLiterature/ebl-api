# TASK-m2m-log.md

## Task: Add M2M Auth0 support for client credentials flow

---

### 2026-06-09 — Initial implementation

**Problem identified:**  
M2M (client credentials) tokens from Auth0 were being rejected by the API because:
1. `required_claims` included `"openid"`, a custom Auth0 Rule claim present only in user-facing tokens — never in client credentials tokens.
2. `Auth0User.authenticate` unconditionally called `fetch_user_profile` → `/userinfo`, which M2M tokens cannot access.
3. Tokens were being requested from the native Auth0 tenant domain instead of the custom domain, causing issuer mismatch.

**Changes made:**
- `ebl/users/infrastructure/auth0.py`: removed `"openid"` from `required_claims`; added M2M branch (detect via `gty == "client-credentials"`) skipping `/userinfo`, returning `{"name": sub}` as profile instead.
- `ebl/tests/users/test_auth0_backend.py`: removed `"openid": True` from `create_token()` payload; added `test_auth_backend_m2m_token`.
- Added `M2M_Auth0_instructions.md` and `M2M_Auth0_manual.md`.

**Test result:** 33 passed, 87% coverage.

---

### 2026-06-09 — Post-review fixes (local)

- Added `"sub"` to `required_claims` to prevent `KeyError` at `access_token["sub"]` (Finding 5).
- Fixed staged vs working-tree divergence: lambdas in staged index → re-staged with named functions (Finding 1).
- Fixed `M2M_Auth0_instructions.md` Step N5: `add-realia` branch / PR #715 → `m2m-changes` (Finding 4).
- Updated stale lambda code snippet in instructions to named-function style.
- Updated `M2M_Auth0_manual.md`: `.env` guidance, sensitive data callouts, token-as-bearer-credential warning.

**Commit:** `f62198d3`

---

### 2026-06-09 — GitHub PR #721 reviews integrated

**Sourcery AI** and **Copilot** left 10 inline threads. Findings recorded in `TASK-m2m-review.md` as Findings 6–12.

Key new findings:
- Coverage gap in the new closure bodies (lines 87, 92) and `fetch_user_profile` (lines 13–17) — no test ever called `user.profile`.
- No negative test for missing `sub`.
- Token file paths in docs pointed at working directory, not `/tmp`.
- Inline `CLIENT_ID`/`CLIENT_SECRET` literals in bash scripts.
- "Dictionary" label in Step 3 missing audience identifier.
- "Command for step 4:" caption off-by-one in manual Section 7.

---

### 2026-06-09 — All findings addressed

**Code changes:**
- Added explicit `sub` guard in `authenticate()`: `sub = access_token.get("sub"); if sub is None: raise falcon.HTTPUnauthorized()`. This is cleaner than relying solely on `required_claims` enforcement by the JWT library.
- Added `import falcon` to `auth0.py`.
- Used the already-validated `sub` variable in the M2M `profile_factory` closure instead of re-indexing `access_token["sub"]`.
- Added three new tests:
  - `test_auth_backend_m2m_token_profile`: verifies `profile == {"name": sub}` and `fetch_user_profile` not called (Finding 7 + 2).
  - `test_auth_backend_non_m2m_profile_calls_userinfo`: verifies `requests.get` is called for regular tokens and profile is returned (Finding 2).
  - `test_auth_backend_missing_sub_is_unauthorized`: verifies missing `sub` → HTTP 401 (Finding 6).
- Added `ProfileCapturingResource` and `create_profile_capturing_client` helpers to enable profile assertions from integration-style tests.

**Documentation changes (Findings 3, 8, 9, 10, 11):**
- All token file paths in `M2M_Auth0_manual.md` changed to `/tmp/token.txt`, `/tmp/token_response.json`, `/tmp/negative_token.txt`.
- Manual Section 7 caption: "Command for step 4:" → "Command for step 5:".
- Instructions Step 3: "Select Dictionary." → "Select the `Dictionary` API (audience: `dictionary-api`).".
- Instructions minimal bash script: inline `CLIENT_ID`/`CLIENT_SECRET` literals → `${M2M_CLIENT_ID:?...}` fail-fast env-var guards.
- Instructions minimal single-command variant: same env-var pattern.
- Instructions Step N4: `new_token_response.json` / `new_token.txt` → `/tmp/new_token_response.json` / `/tmp/new_token.txt`.

**Test result:** 36 passed, 100% coverage on `ebl/users/infrastructure/auth0.py`.

---

### Remaining before merge

- Remove `TASK-m2m-todo.md`, `TASK-m2m-log.md`, `TASK-m2m-review.md` in a clean-up commit (Finding 12).
