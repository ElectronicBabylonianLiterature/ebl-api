# ebl-api Auth Fix Handoff (Post-Auth0 Rotation)

This handoff is validated against current backend code in `ebl-api`.

Please implement a **code-side fix only** for authorization after Auth0 rotation.  
Do **not** rely on restoring old Auth0 Rules/Actions.

## Backend-Verified Problem Summary

Users can authenticate, but protected write endpoints may return `403` (example: `POST /fragments/{number}/edition`).

Observed token shape after rotation:
- `scope`: often identity/OIDC-only values (`openid profile offline_access`)
- `permissions`: contains API authorization values (`transliterate:fragments`, `lemmatize:fragments`, etc.)

Current authorization path:
- endpoint decorators call `require_scope(...)` in `ebl/users/web/require_scope.py`
- `require_scope` checks `user.has_scope(Scope.from_string(required_scope))`
- for Auth0 users, `has_scope` calls `Auth0User.get_scopes()` in `ebl/users/infrastructure/auth0.py`
- `get_scopes()` currently parses only `self._access_token["scope"].split()`

As a result, permissions present only in `permissions` are invisible to authorization.

## Root Cause

`Auth0User.get_scopes()` ignores `permissions` and depends on `scope` only.

Additional robustness issue found during investigation:
- `self._access_token["scope"]` direct indexing can raise `KeyError` if `scope` is absent.
- `Auth0Backend` does **not** require a `scope` claim (required claims: `exp`, `iat`, `openid`), so missing `scope` is possible.

## Required Backend Fix

Update `Auth0User.get_scopes()` in `ebl/users/infrastructure/auth0.py` to read **both** claims safely.

1. Gather candidate tokens from:
   - `scope` claim as a space-separated string (`scope.split()` if string)
   - `permissions` claim as a list/tuple of strings (if iterable of strings)
2. Merge and deduplicate tokens.
3. Preserve existing behavior for conversion/filtering:
   - apply existing `prefix` and `suffix` filtering
   - convert with `Scope.from_string(token)`
   - ignore invalid/unknown values (`ValueError`)
4. Be defensive for malformed/missing claims:
   - missing `scope` should behave as empty scope set
   - missing/null/non-list `permissions` should be ignored
   - non-string list items in `permissions` should be ignored

### Suggested implementation shape

- `scope_tokens = raw_scope.split()` when `raw_scope` is `str`, else `[]`
- `permission_tokens = [p for p in raw_permissions if isinstance(p, str)]` when `raw_permissions` is `list` or `tuple`, else `[]`
- iterate over `dict.fromkeys(scope_tokens + permission_tokens)` for stable deduplication
- apply existing prefix/suffix + `Scope.from_string(...)` + `ValueError` skip logic

No Auth0 dashboard/rule/action change is required for this backend fix.

## Tests to Add/Update

Primary file: `ebl/tests/users/test_auth0_user.py`.

Add/adjust tests for:

1. **Permissions-only authorization works**
   - token with empty/minimal `scope`
   - token with `permissions=["transliterate:fragments"]`
   - `has_scope(Scope.TRANSLITERATE_FRAGMENTS)` is `True`

2. **Merged + deduplicated claims**
   - same permission appears in both `scope` and `permissions`
   - returned scopes include it once

3. **Prefix/suffix filtering on permissions-derived scopes**
   - `get_scopes(prefix="read:", suffix="-fragments")` behaves correctly when matching values originate from `permissions`

4. **Unknown/invalid permissions are ignored safely**
   - invalid strings and non-string values do not crash and are skipped

5. **Legacy scope-only behavior unchanged**
   - existing scope-only tests stay green

6. **Missing `scope` does not crash** (recommended)
   - token with only `permissions`
   - `get_scopes()` and `has_scope(...)` work without `KeyError`

Optional integration-style coverage:
- expand `ebl/tests/users/test_require_scope.py` with a case where `Auth0User` is instantiated from permissions-only token and guarded endpoint returns `200`.

## Similar Issues Scan (Backend)

Investigation result: no second parser for Auth0 token permissions/scope was found; auth scope resolution is centralized in `Auth0User.get_scopes()`.

Potential adjacent risks to verify while implementing:
- any tests or code assuming `scope` claim always exists
- any future code added that directly indexes token claims (`token["..."]`) without type guards

## Acceptance Criteria

- `POST /fragments/{number}/edition` succeeds when required permission is present in `permissions` even if absent from `scope`.
- Legacy `scope`-based tokens continue to authorize exactly as before.
- Auth/user tests pass, including new `permissions`-based coverage.

## Non-Goals

- Do not modify frontend behavior.
- Do not require reintroducing old Auth0 Rules/Actions.
- Do not change endpoint-level required scope decorators.
