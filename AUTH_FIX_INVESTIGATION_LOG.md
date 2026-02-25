# Auth Fix Investigation Log

Date: 2026-02-25
Repository: `ElectronicBabylonianLiterature/ebl-api`
Branch: `master`

## Scope of Work

- Copied the provided frontend-generated handoff into a new backend-facing handoff file.
- Investigated backend authorization flow and tests.
- Refined the handoff to match current backend implementation and edge cases.
- Did **not** modify runtime/backend code.

## Files Created/Updated

- Created: `AUTH_FIX_HANDOFF.md`
- Updated: `AUTH_FIX_HANDOFF.md` (backend-verified details and fix guidance)
- Created: `AUTH_FIX_INVESTIGATION_LOG.md`

## Backend Findings

1. Authorization checks for protected endpoints flow through:
   - `ebl/users/web/require_scope.py` -> `user.has_scope(...)`
   - `ebl/users/infrastructure/auth0.py` -> `Auth0User.has_scope(...)` -> `get_scopes()`

2. Root cause confirmed:
   - `Auth0User.get_scopes()` currently parses only `self._access_token["scope"].split()`
   - `permissions` claim is ignored.

3. Adjacent robustness risk identified:
   - direct indexing `self._access_token["scope"]` may raise `KeyError` when `scope` is absent.
   - `Auth0Backend` required claims are `exp`, `iat`, `openid` (not `scope`), so missing `scope` is possible.

4. Similar-issue scan result:
   - No other backend auth token scope parser was found.
   - Scope interpretation appears centralized in `Auth0User.get_scopes()`.

## Suggested Code Change (not applied)

- In `Auth0User.get_scopes()`, merge scopes from both:
  - `scope` (space-separated string)
  - `permissions` (list/tuple of strings)
- Deduplicate merged tokens.
- Preserve existing prefix/suffix filter behavior.
- Preserve existing skip-on-`ValueError` behavior for unknown scopes.
- Handle missing/malformed claims defensively.

## Suggested Test Additions (not applied)

- Extend `ebl/tests/users/test_auth0_user.py` with:
  - permissions-only token grants expected scope
  - mixed claims merge + deduplicate
  - prefix/suffix filtering using permissions-derived values
  - unknown/invalid permission values ignored safely
  - scope-only behavior unchanged
  - missing `scope` does not crash

- Optionally extend `ebl/tests/users/test_require_scope.py` with a permissions-only guarded endpoint success case.

## Constraints Observed

- No backend code modifications were made, per request.
- No Auth0 dashboard/config changes were proposed as required for the fix.

## Implementation Update

Date: 2026-02-25

- Implemented backend fix in `ebl/users/infrastructure/auth0.py`:
   - `Auth0User.get_scopes()` now reads both `scope` and `permissions` claims.
   - Merges token values with deduplication.
   - Preserves prefix/suffix filtering and unknown-scope skipping behavior.
   - Handles missing/malformed `scope`/`permissions` without exceptions.

- Added/updated tests:
   - `ebl/tests/users/test_auth0_user.py`
   - `ebl/tests/users/test_require_scope.py`

- Updated documentation:
   - `README.md` (Auth0 claim handling and Rules/Actions guidance)
   - `SECRET_ROTATION_NOTE.md` (post-rotation backend authorization note)

## Verification

Executed:

`poetry run pytest ebl/tests/users/test_auth0_user.py ebl/tests/users/test_require_scope.py`

Result:

- 21 passed
- 0 failed
