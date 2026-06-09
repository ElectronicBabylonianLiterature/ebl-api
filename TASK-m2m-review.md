# TASK-m2m-review.md

## Summary

This review covers the `m2m-changes` branch. The change adds M2M (Machine-to-Machine / client credentials) Auth0 token support to the API backend. Two code files and two documentation files were changed or added.

**Verified locally:** `poetry run pytest ebl/tests/users/ --cov=ebl.users.infrastructure.auth0 --cov-report=term-missing` — 36 passed, **100% coverage**.

---

## GitHub PR Reviews — PR #721

Two automated reviewers left feedback: **Sourcery AI** (2026-06-09T16:17) and **Copilot** (2026-06-09T16:22).

---

## Findings

---

### Finding 1 — ~~Staged vs. working-tree divergence (lambda vs. named function)~~ RESOLVED

The staged index previously contained lambdas; the correct named-function version was re-staged and committed.

---

### Finding 2 — ~~Coverage is 87%, below required 100%~~ RESOLVED

Three new tests added covering all previously uncovered lines:
- `test_auth_backend_m2m_token_profile`: triggers M2M `profile_factory`, asserts `profile == {"name": sub}`, asserts `fetch_user_profile` not called.
- `test_auth_backend_non_m2m_profile_calls_userinfo`: triggers non-M2M `profile_factory`, mocks `requests.get`, asserts it is called and profile is returned (covers lines 13–17 and 92).
- Coverage is now **100%** (57/57 statements).

---

### Finding 3 — ~~Token files not in `.gitignore`; prefer `/tmp`~~ RESOLVED

All token file paths in `M2M_Auth0_manual.md` and `M2M_Auth0_instructions.md` changed to `/tmp/token.txt`, `/tmp/token_response.json`, `/tmp/negative_token.txt`, `/tmp/new_token_response.json`, `/tmp/new_token.txt`. Notes updated to instruct deletion immediately after use.

---

### Finding 4 — ~~Documentation references wrong branch (`add-realia`, PR #715)~~ RESOLVED

`M2M_Auth0_instructions.md` Step N5 now references the `m2m-changes` branch.

---

### Finding 5 — ~~`access_token["sub"]` raises `KeyError` if `sub` is absent~~ RESOLVED

Revised approach: instead of relying on `required_claims` enforcement by the JWT library (which proved insufficient — `falcon_auth` passed through tokens without `sub` causing a 500), an explicit guard was added at the top of `authenticate()`:

```python
sub = access_token.get("sub")
if sub is None:
    raise falcon.HTTPUnauthorized()
```

This guarantees a clean 401 for any token missing `sub`, regardless of library behaviour.

---

### Finding 6 — ~~Missing negative test for absent `sub` claim~~ RESOLVED

Added `test_auth_backend_missing_sub_is_unauthorized`: uses `overrides={"sub": None}` to drop the claim, asserts HTTP 401. The explicit guard in `authenticate()` (Finding 5) makes this return 401 cleanly.

---

### Finding 7 — ~~`test_auth_backend_m2m_token` does not assert M2M-specific behaviour~~ RESOLVED

Added `test_auth_backend_m2m_token_profile` which:
- Uses `Mock()` as `set_user` and patches `fetch_user_profile`.
- Asserts `set_user.assert_called_once_with(sub)` — confirms `sub` is extracted.
- Asserts `mock_fetch.assert_not_called()` — confirms `/userinfo` is not called.
- Asserts `resource.captured_profile == {"name": sub}` via `ProfileCapturingResource`.

---

### Finding 8 — ~~Auth0 instructions: "Dictionary" label ambiguous~~ RESOLVED

Step 3 updated to: *"Select the `Dictionary` API (audience: `dictionary-api`)."*

---

### Finding 9 — ~~Manual: "Command for step 4" caption is wrong (off-by-one)~~ RESOLVED

Caption changed to "Command for step 5:" (step 5 in the numbered list is the re-run write test step).

---

### Finding 10 — ~~Instructions bash script has inline secret literals~~ RESOLVED

Minimal API Test Script updated to use `${M2M_CLIENT_ID:?M2M_CLIENT_ID is not set}` and `${M2M_CLIENT_SECRET:?M2M_CLIENT_SECRET is not set}`. Minimal single-command variant updated to use `${M2M_CLIENT_ID:?}` / `${M2M_CLIENT_SECRET:?}` with a `source .env` preamble.

---

### Finding 11 — ~~Instructions: Step N4 token files written to working directory~~ RESOLVED

Step N4 now writes to `/tmp/new_token_response.json` and reads from `/tmp/new_token.txt` consistently.

---

### Finding 12 — `TASK-m2m-review.md` must be removed before merge

**Severity:** Low | **Source:** Sourcery AI (overall comment), Copilot ([r3382218008](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/721#discussion_r3382218008))

**Description:**  
Both reviewers flag that this file is an internal task artifact and should not be shipped to `master`. The project instructions also require removing `TASK-*` files before merging.

**Recommendation:**  
Delete this file in a final clean-up commit before the PR is merged.

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
| All 33 user tests pass | ✓ Now 36 tests, 100% coverage. |

---

## Severity Summary

| # | Finding | Severity | Status | Source |
|---|---|---|---|---|
| 1 | Staged vs. working-tree lambda divergence | Medium | **Resolved** | Local |
| 2 | Coverage 87% — lines 13–17, 87, 92 uncovered | High | **Resolved** | Local + Sourcery + Copilot |
| 3 | Token files not in `.gitignore`; prefer `/tmp` | Low | **Resolved** | Local + Copilot |
| 4 | Documentation references wrong branch/PR | Low | **Resolved** | Local |
| 5 | `access_token["sub"]` KeyError on missing claim | Low | **Resolved** | Local |
| 6 | Missing negative test for absent `sub` claim | Medium | **Resolved** | Sourcery |
| 7 | M2M test only asserts HTTP 200, not behaviour | Medium | **Resolved** | Sourcery + Copilot |
| 8 | Instructions: "Dictionary" label ambiguous | Low | **Resolved** | Sourcery |
| 9 | Manual: "Command for step 4" caption off-by-one | Low | **Resolved** | Sourcery |
| 10 | Instructions script has inline secret literals | Low | **Resolved** | Copilot |
| 11 | Instructions Step N4 writes token files to working dir | Low | **Resolved** | Copilot |
| 12 | `TASK-m2m-review.md` must be removed before merge | Low | Open | Sourcery + Copilot |

**All blockers resolved. Remaining before merge: Finding 12 (remove task files).**

---

*Reminder: Remove this file (`TASK-m2m-review.md`) before merging the PR.*
