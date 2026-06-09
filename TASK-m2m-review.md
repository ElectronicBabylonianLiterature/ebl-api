# TASK-m2m-review.md

## Summary

This review covers the `m2m-changes` branch. The change adds M2M (Machine-to-Machine / client credentials) Auth0 token support to the API backend. Two code files and two documentation files were changed or added.

**Verified locally:** `poetry run pytest ebl/tests/users/ --cov=ebl.users.infrastructure.auth0 --cov-report=term-missing` — 33 passed, 87% coverage.

---

## Findings

---

### Finding 1 — Staged vs. working-tree divergence (lambda vs. named function)

**Severity:** Medium

**Description:**  
The staged (`git diff --cached`) version of `auth0.py` uses lambda assignments:

```python
if is_m2m:
    profile_factory = lambda: {"name": access_token["sub"]}
else:
    profile_factory = lambda: fetch_user_profile(self.issuer, req.auth)
```

The working tree version uses named `def` blocks (the version currently on disk). The named-function style is the correct one. Committing the staged version would introduce flake8 E731 violations (`do not assign a lambda expression`) and diverge from the project's style. The staged index must be updated to match the working tree before committing.

**Reproduction Steps:**  
`git diff --cached ebl/users/infrastructure/auth0.py` shows lambdas.  
`git diff ebl/users/infrastructure/auth0.py` (unstaged) shows named functions.

**Recommendation:**  
Unstage the current version and re-stage the working-tree version:  
`git restore --staged ebl/users/infrastructure/auth0.py && git add ebl/users/infrastructure/auth0.py`

---

### Finding 2 — Coverage is 87%, below required 100%

**Severity:** High

**Description:**  
Coverage report after the change:

```
Name                                Stmts   Miss  Cover   Missing
ebl/users/infrastructure/auth0.py      53      7    87%   13-17, 87, 92
```

- **Lines 13–17**: The body of `fetch_user_profile` (the HTTP call to Auth0's `/userinfo` endpoint) is never executed in the test suite.
- **Line 87**: The `return {"name": access_token["sub"]}` body inside the M2M `profile_factory` closure.
- **Line 92**: The `return fetch_user_profile(...)` body inside the non-M2M `profile_factory` closure.

The project rule is: *"Ensure that coverage is 100% after changes in affected code."*

Lines 87 and 92 are directly inside the new code introduced by this change. `fetch_user_profile` (lines 13–17) is unchanged, but it was previously reachable through the (now removed) inline lambda in the old `authenticate`. Its coverage was already a pre-existing gap — though the refactor made it more explicit.

**Reproduction Steps:**  
```
poetry run pytest ebl/tests/users/ --cov=ebl.users.infrastructure.auth0 --cov-report=term-missing
```

**Recommendation:**  
Add tests to cover all three gaps:

1. `test_auth_backend_m2m_token` must trigger `user.profile` to cover line 87. This requires the test to access the returned `Auth0User`, which the current `simulate_get` helper does not expose. One option is to capture the user object via the `set_user` callback or to test `Auth0User` with the M2M `profile_factory` directly in `test_auth0_user.py`.
2. Cover `fetch_user_profile` (lines 13–17) by mocking `requests.get` and calling `fetch_user_profile` directly, or by triggering the non-M2M path and calling `profile` on the returned `Auth0User`.
3. The non-M2M `profile_factory` body (line 92) can be covered together with point 2.

---

### Finding 3 — `token.txt` and `token_response.json` not in `.gitignore`

**Severity:** Low

**Description:**  
`M2M_Auth0_manual.md` instructs operators to save the raw JWT to `token.txt` and the full token response to `token_response.json` on disk. It warns these must never be committed. However, neither filename appears in `.gitignore`, meaning a developer following the manual could accidentally stage them.

**Reproduction Steps:**  
`grep -E "token\.txt|token_response" .gitignore` → no match.

**Recommendation:**  
Add to `.gitignore`:
```
token.txt
token_response.json
negative_token.txt
```

---

### Finding 4 — ~~Documentation references wrong branch (`add-realia`, PR #715)~~ RESOLVED

`M2M_Auth0_instructions.md` Step N5 now references the `m2m-changes` branch. The stale PR #715 / `add-realia` references and the option A/B split have been removed.

---

### Finding 5 — ~~`access_token["sub"]` raises `KeyError` if `sub` is absent~~ RESOLVED

`"sub"` has been added to `required_claims` in `Auth0Backend.__init__`. The JWT library now rejects tokens missing `sub` with a 401 before `authenticate` is ever called, eliminating the `KeyError` at the source.

---

## Passing Checks

| Check | Result |
|---|---|
| Core logic correctness — removing `openid` from `required_claims` | ✓ Correct. `openid` was a non-standard Auth0 Rule claim absent in client-credentials tokens. |
| M2M detection via `gty == "client-credentials"` | ✓ Correct. This is the standard Auth0 M2M identifier; claim is RS256-signed and cannot be forged. |
| M2M path skips `/userinfo` | ✓ Correct. M2M tokens have no user identity; calling `/userinfo` would fail. |
| M2M `profile["name"]` set to `sub` | ✓ Correct. `sub` is the client ID, usable as audit identity (`ebl_name`). |
| `verify_claims` alignment | ✓ `required_claims=["exp","iat"]` now matches `verify_claims=["signature","exp","iat"]`. |
| No secrets in committed files | ✓ All credential fields are placeholders. |
| flake8 (working tree) | ✓ No violations. |
| mypy errors introduced by this change | ✓ None. All mypy errors in the file are pre-existing. |
| All 33 user tests pass | ✓ |

---

## Severity Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | Staged vs. working-tree lambda divergence | Medium | Open |
| 2 | Coverage 87% — lines 13–17, 87, 92 uncovered | High | Open |
| 3 | `token.txt` / `token_response.json` not in `.gitignore` | Low | Open |
| 4 | Documentation references wrong branch/PR | Low | **Resolved** |
| 5 | `access_token["sub"]` KeyError on missing claim | Low | **Resolved** |

**Blockers before merge:** Findings 1 and 2.

---

*Reminder: Remove this file (`TASK-m2m-review.md`) before merging the PR.*
