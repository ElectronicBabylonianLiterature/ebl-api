Here's a more detailed implementation instruction suitable for an internal task or runbook.

# Instructions: Create and Configure a Dedicated Auth0 M2M Application for the Bibliography Partner API

## Purpose

Create a dedicated Auth0 Machine-to-Machine (M2M) application for the Bibliography Partner API integration.

A separate application must be used instead of shared credentials in order to:

* Identify which partner is creating or modifying bibliography records.
* Support independent credential rotation.
* Allow access to be revoked for a single partner without affecting others.
* Improve auditing and troubleshooting.
* Follow the principle of least privilege.

---

# Prerequisites

Before beginning, ensure that:

* You have administrative access to the Auth0 tenant.
* The Bibliography API already exists as an Auth0 API (Resource Server).
* The required scopes are available or can be added.
* You know the name of the partner that will use the integration.

---

# Step 1: Verify Existing Bibliography API Configuration

1. Log in to the Auth0 Dashboard.

2. Navigate to:

   Applications → APIs

3. Locate the Bibliography API.

4. Verify that the API exists and note:

   * API Name
   * Identifier (Audience)

5. Confirm that the following scopes exist:

   * `read:bibliography`
   * `write:bibliography`

### Validation

All scopes should be visible under the API permissions list:

| Scope                           | Description                        |
| ------------------------------- | -----------------------------------|
| `read:bibliography`             | Read bibliography records.         |
| `write:bibliography`            | Write bibliography records.        |

### If a Scope Is Missing

Create the missing scope with the corresponding description.

---

# Step 2: Create a New M2M Application

1. Navigate to:

   Applications → Applications

2. Click:

   Create Application

3. Enter an application name.

### Naming Convention

Used:

```
M2M Bibliography
```

4. Select:

   Machine to Machine Applications

5. Create the application.

6. On the **Settings** tab that opens, the only fields relevant for an M2M application are:

   | Field | Action |
   |---|---|
   | **Name** | Already set. |
   | **Description** | Optional but recommended — add the partner name and purpose, e.g. `"Bibliography partner integration for [Partner Name]"`. Max 140 characters. |
   | **Client ID** | Auto-generated. Copy and store securely. |
   | **Client Secret** | Auto-generated. Copy and store securely. The secret is **not** base64-encoded. |
   | **Application Type** | Already set to "Machine to Machine". |

   All other fields (Application URIs, Allowed Callback URLs, Logout URLs, Web Origins, CORS, Cross-Origin Authentication, ID Token Expiration, Refresh Token settings) are irrelevant for the client credentials flow and can be left empty/at their defaults. M2M applications do not redirect users and do not use refresh tokens.

7. Click **Save Changes**.

### Validation

Verify that:

* The application appears in the Applications list.
* A Client ID has been generated.
* A Client Secret has been generated.

Record both values securely for later distribution. Do not share them over unencrypted channels.

---

# Step 3: Authorize the Application Against the Bibliography API

1. After creating the application, Auth0 should display a list of APIs.

2. Select Dictionary.

3. Authorize the application.

### Validation

The Bibliography API should now appear under:

Applications → [Application Name: M2M Bibliography] → APIs

---

# Step 4: Assign Permissions

Enable the following permissions:

* `read:bibliography`
* `write:bibliography`

Save the configuration.

### Validation

Verify that all permissions are enabled and saved.

---

# Step 5: Test Token Issuance

Obtain an access token using the Client Credentials flow.

> **Important:** Always request the token from the **custom domain** (`https://auth.ebl.lmu.de/`), not the native Auth0 domain. The token's `iss` claim must match the `AUTH0_ISSUER` configured in the API (`https://auth.ebl.lmu.de/`). Using the native domain (`electronic-babylonian-literature.eu.auth0.com`) produces an issuer mismatch and the API will reject the token.

Example request:

```bash
curl --request POST \
  --url https://auth.ebl.lmu.de/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"CLIENT_ID",
    "client_secret":"CLIENT_SECRET",
    "audience":"dictionary-api",
    "grant_type":"client_credentials"
}'
```

### Validation

Verify that:

* HTTP status code is 200.
* An access token is returned.
* No authorization errors are present.

---

# Step 6: Verify Token Claims

Decode the JWT.

Check that:

* Audience matches the Bibliography API.
* Issuer is correct.
* Expiration is reasonable.
* Permissions claim is present.

Expected claims:

```json
{
  "iss": "https://auth.ebl.lmu.de/",
  "aud": "dictionary-api",
  "gty": "client-credentials",
  "permissions": [
    "write:bibliography",
    "read:bibliography"
  ]
}
```

> **Note:** The `iss` claim must be `https://auth.ebl.lmu.de/` (the custom domain). If it shows `https://electronic-babylonian-literature.eu.auth0.com/`, the token was requested from the wrong domain and will be rejected by the API.

### Validation

All required permissions must be present.

---

# Step 7: Perform Authorization Checks

Using the generated token, verify access to each relevant endpoint.

## Bibliography Read Endpoint

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://www.ebl.lmu.de/api/bibliography/LS139
```

Expected result:

* HTTP 200 with bibliography record JSON.
* Note: this endpoint is public — it also returns 200 without a token.

## Bibliography Write Endpoint

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"TEST-ID","type":"article-journal","title":"Test","author":[{"family":"Test","given":"Author"}],"issued":{"date-parts":[[2026]]}}' \
  https://www.ebl.lmu.de/api/bibliography
```

Expected result:

* HTTP 201 Created.
* Bibliography record created.

### Validation

Each endpoint should authorize successfully using the new token.

---

# Step 8: Negative Permission Test

Confirm that authorization enforcement works correctly.

Procedure:

1. Temporarily remove one permission.
2. Generate a new token.
3. Call the corresponding endpoint.

Expected result:

* API returns 403 Forbidden or equivalent authorization error.

Restore the permission afterward.

### Validation

The API must reject operations when the corresponding permission is missing.

---

# Step 9: Documentation

Document the following information:

## Application Details

* Application Name
* Client ID
* Creation Date
* Responsible Partner

## Assigned Permissions

* read:bibliography
* write:bibliography

## Operational Notes

* How credentials are distributed.
* How credentials are rotated.
* How access is revoked.
* How to create additional partner-specific applications.

---

# Completion Checklist

* [x] Bibliography API exists.
* [x] Required scopes exist.
* [x] Dedicated M2M application created.
* [x] Application authorized against Bibliography API.
* [x] All permissions assigned.
* [x] Client Credentials flow tested successfully — token from `https://auth.ebl.lmu.de/oauth/token` ✓
* [x] JWT contains expected `iss` claim (`https://auth.ebl.lmu.de/`) ✓
* [x] Backend fix deployed to local API (`openid` removed, M2M profile handling added) ✓
* [x] Write endpoint authorized successfully (HTTP 201) ✓
* [ ] Negative authorization test completed (requires manual permission removal in Auth0 dashboard — see Step N4).
* [ ] Backend fix merged to production.
* [ ] Configuration documented.
* [ ] Credentials delivered to the partner through the approved channel.

## Expected Final State

A dedicated partner-specific Auth0 M2M application exists and can securely access the Bibliography Partner API with the following permissions:

* `read:bibliography`
* `write:bibliography`

The integration is independently manageable, auditable, and does not rely on shared credentials.


---

Here’s a minimal **bash script (curl-based)** that:

1. fetches a token via Client Credentials flow
2. calls one bibliography endpoint (example: read/export/check—replace URL)

---

## Minimal API Test Script

```bash
#!/usr/bin/env bash

# === CONFIG ===
AUTH0_DOMAIN="https://auth.ebl.lmu.de"
CLIENT_ID="YOUR_CLIENT_ID"
CLIENT_SECRET="YOUR_CLIENT_SECRET"
AUDIENCE="dictionary-api"

# Bibliography API endpoint
API_URL="https://www.ebl.lmu.de/api/bibliography"

# === 1. GET ACCESS TOKEN ===
TOKEN_RESPONSE=$(curl -s --request POST \
  --url "$AUTH0_DOMAIN/oauth/token" \
  --header 'content-type: application/json' \
  --data "{
    \"client_id\": \"$CLIENT_ID\",
    \"client_secret\": \"$CLIENT_SECRET\",
    \"audience\": \"$AUDIENCE\",
    \"grant_type\": \"client_credentials\"
  }")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to obtain access token"
  echo "$TOKEN_RESPONSE"
  exit 1
fi

echo "Token acquired"

# === 2. CALL API ===
curl -s -X GET "$API_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Minimal variant (single command, no variables)

If you just want the shortest possible check:

```bash
TOKEN=$(curl -s --request POST \
  --url https://auth.ebl.lmu.de/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"YOUR_CLIENT_ID",
    "client_secret":"YOUR_CLIENT_SECRET",
    "audience":"dictionary-api",
    "grant_type":"client_credentials"
  }' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" \
     https://www.ebl.lmu.de/api/bibliography/LS139
```

---

## Quick notes

* Requires `jq` installed (`brew install jq` / `apt install jq`)
* Replace:

  * Auth0 domain
  * Client ID/secret
  * API audience
  * API endpoint
* Works for any of the scopes (`read`, `create`, etc.) depending on endpoint

---

# Test Results & Backend Fix Required

## Test Environment

* API: `https://www.ebl.lmu.de/api` (production) and `http://localhost:8001` (local)
* Auth0 custom domain: `https://auth.ebl.lmu.de/`
* Audience: `dictionary-api`
* Token source: client credentials flow, verified JWT

## JWT Verification (Step 6) — PASS

Token requested from `https://auth.ebl.lmu.de/oauth/token`:

| Claim | Value | Status |
|---|---|---|
| `iss` | `https://auth.ebl.lmu.de/` | ✓ |
| `aud` | `dictionary-api` | ✓ |
| `gty` | `client-credentials` | ✓ |
| `permissions` | `["write:bibliography", "read:bibliography"]` | ✓ |

## Endpoint Authorization Results (Steps 7 & 8)

| Test | Endpoint | Token | HTTP Status | Result |
|---|---|---|---|---|
| Read with token | `GET /api/bibliography/LS139` | Yes | 200 | ✓ Pass |
| Read without token | `GET /api/bibliography/LS139` | No | 200 | ✓ Pass (public endpoint) |
| Write with token (local) | `POST /bibliography` | Yes | **201** | ✓ Pass |
| Negative write test | `POST /bibliography` | No `write:bibliography` | — | ⏳ Pending (manual step in Auth0 dashboard) |

## Root Cause of Write 403: Two Issues Found

### Issue 1: Issuer mismatch (primary blocker)

The M2M token was requested from the native Auth0 domain (`https://electronic-babylonian-literature.eu.auth0.com/`), producing a token with `iss = https://electronic-babylonian-literature.eu.auth0.com/`. The API validates against `AUTH0_ISSUER = https://auth.ebl.lmu.de/` (the custom domain). The mismatch causes `InvalidIssuerError`, JWT validation fails, and `MultiAuthBackend` falls back to `NoneAuthBackend(Guest)` → 403.

**Fix:** Always request tokens from `https://auth.ebl.lmu.de/oauth/token`.

### Issue 2: `openid` required claim (latent bug, now fixed)

The backend (`ebl/users/infrastructure/auth0.py`) was configured with:

```python
required_claims=["exp", "iat", "openid"],
```

The `openid` entry is a **custom claim** injected by an Auth0 Rule/Action into user-facing tokens only. M2M (client credentials) tokens never contain this claim — Auth0 does not support `openid` in the client credentials flow. This would block M2M tokens even with the correct issuer.

Additionally, `Auth0User.profile` called the `/userinfo` endpoint, which M2M tokens cannot access (there is no user identity).

**Fix:** Both issues resolved in `ebl/users/infrastructure/auth0.py` (see Required Backend Fix below).

## Backend Fix — DONE ✓

Both issues were fixed in `ebl/users/infrastructure/auth0.py`:

### 1. Removed `"openid"` from `required_claims`

```python
required_claims=["exp", "iat"],
```

### 2. M2M tokens skip `/userinfo` call

```python
def authenticate(self, req, resp, resource):
    access_token = super().authenticate(req, resp, resource)
    self._set_user(access_token["sub"])
    is_m2m = access_token.get("gty") == "client-credentials"
    if is_m2m:

        def profile_factory():
            return {"name": access_token["sub"]}

    else:

        def profile_factory():
            return fetch_user_profile(self.issuer, req.auth)

    return Auth0User(access_token, profile_factory)
```

### 3. Tests updated

* `"openid": True` removed from `create_token()` in `test_auth0_backend.py`
* `test_auth_backend_m2m_token` added — verifies a token with `gty=client-credentials` is accepted (HTTP 200)
* All 7 backend tests pass ✓

## Remaining Steps

### Completed in this run

* Token was requested from `https://auth.ebl.lmu.de/oauth/token`.
* Token claims were verified (`iss`, `aud`, `gty`, permissions).
* Local write check succeeded with HTTP 201.

> Keep token and client secret out of git. Do not paste them into issues, PRs, or chat logs.

---

### Step N4: Run the negative permission test (Step 8)

1. In the Auth0 Dashboard, navigate to:
   Applications → Applications → **M2M Bibliography** → APIs tab.
2. Click the **M2M Bibliography** entry and remove `write:bibliography`.
3. Save.
4. Request a **new token** (the old token still contains old permissions until expiry):

   ```bash
   curl -s --request POST \
     --url https://auth.ebl.lmu.de/oauth/token \
     --header 'content-type: application/json' \
     --data '{
       "client_id":"CLIENT_ID",
       "client_secret":"CLIENT_SECRET",
       "audience":"dictionary-api",
       "grant_type":"client_credentials"
     }' > new_token_response.json

   cat new_token_response.json | jq -r '.access_token' > new_token.txt
   ```
5. Run the write test again:

   ```bash
   NEW_TOKEN=$(cat new_token.txt | tr -d '\n')

   curl -s -w "HTTP %{http_code}\n" \
     -X POST \
     -H "Authorization: Bearer $NEW_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"id":"M2M-TEST-NEGATIVE","type":"article-journal","title":"Should Fail","author":[{"family":"Test","given":"M2M"}],"issued":{"date-parts":[[2026]]}}' \
     http://localhost:8001/bibliography
   ```

   Expected: **HTTP 403 Forbidden**.

6. Restore `write:bibliography` in Auth0 and verify it is saved.

---

### Step N5: Deploy the backend fix to production

The backend fix lives on the `m2m-changes` branch. It needs to reach `master` before production will work.

Open a PR from `m2m-changes` into `master` on GitHub. Ensure all pre-commit gates pass before merging.

In either case, the pre-commit gates must pass before merging:

```bash
task format
task test
poetry run pytest ebl/tests/users/ --cov=ebl/users/infrastructure/auth0 --cov=ebl/users/domain --cov-report=term-missing
poetry run flake8 ebl/users/infrastructure/auth0.py ebl/tests/users/test_auth0_backend.py --max-line-length=120
poetry run mypy ebl/users/infrastructure/auth0.py --ignore-missing-imports
```

---

### Step N6: Re-run write test against production

After the fix is deployed:

```bash
TOKEN=$(cat token.txt | tr -d '\n')

curl -s -o /tmp/prod_write_result.json -w "HTTP %{http_code}\n" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"M2M-TEST-PROD","type":"article-journal","title":"M2M Production Write Test","author":[{"family":"Test","given":"M2M"}],"issued":{"date-parts":[[2026]]}}' \
  https://www.ebl.lmu.de/api/bibliography

cat /tmp/prod_write_result.json
```

Expected: HTTP 201.

> **Cleanup:** Remove the test record `M2M-TEST-PROD` from the production database after verifying.
