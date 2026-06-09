# eBL M2M Auth0 Manual (Bibliography API)

## 1. Purpose
This manual explains how to configure, validate, and operate a dedicated Auth0 Machine-to-Machine (M2M) application for bibliography access in eBL.

Use this for:
- Partner-specific credentials
- Least-privilege authorization
- Auditable and revocable API access

---

## 2. eBL Reference Values (Non-Secret)
- Auth0 custom domain: `https://auth.ebl.lmu.de`
- API audience: `dictionary-api`
- Production API base: `https://www.ebl.lmu.de/api`
- Local API base: `http://localhost:8001`
- Required bibliography permissions:
  - `read:bibliography`
  - `write:bibliography`

Important:
- Always request tokens from the custom domain above.
- Tokens requested from the native Auth0 tenant domain will fail issuer validation in this API setup.

---

## 3. Quick Start (If App Already Exists)
1. Confirm M2M app has `read:bibliography` and `write:bibliography`.
2. Request token from `https://auth.ebl.lmu.de/oauth/token`.
3. Decode JWT and verify:
   - `iss = https://auth.ebl.lmu.de/`
   - `aud = dictionary-api`
   - `gty = client-credentials`
   - `permissions` include both bibliography permissions.
4. Test write on local API (`POST /bibliography`) and expect HTTP 201.
5. Run negative test by removing `write:bibliography` temporarily and expect HTTP 403.

---

## 4. Full Procedure

### 4.1 Verify API in Auth0
1. Open Auth0 Dashboard.
2. Go to `Applications -> APIs`.
3. Open the Bibliography API and confirm:
   - Identifier is `dictionary-api`.
   - Scopes include `read:bibliography` and `write:bibliography`.

### 4.2 Create/Validate M2M Application
1. Go to `Applications -> Applications`.
2. Create or open the app (example name: `M2M Bibliography`).
3. Ensure `Application Type` is `Machine to Machine`.
4. Copy the values below and store them **only** in a `.env` file (or equivalent secrets manager). Never store them in plain-text files, scripts, or source control:

> **SENSITIVE — treat as passwords:**
> - `CLIENT_ID` — identifies the application (not secret on its own, but combined with the secret it grants API access)
> - `CLIENT_SECRET` — **secret**. Anyone holding this can obtain valid API tokens. Rotate immediately if exposed.

Example `.env` (add to `.gitignore`):
```
M2M_CLIENT_ID=your-client-id-here
M2M_CLIENT_SECRET=your-client-secret-here
M2M_AUDIENCE=dictionary-api
M2M_AUTH0_DOMAIN=https://auth.ebl.lmu.de
```

Load the variables before running any commands:
```bash
source .env
```

Notes:
- Callback URLs, logout URLs, CORS/web origins, refresh token settings are not needed for client credentials flow.

### 4.3 Authorize API and Assign Permissions
1. In the M2M application, open the `APIs` tab.
2. Authorize access to `dictionary-api`.
3. Enable permissions:
   - `read:bibliography`
   - `write:bibliography`
4. Save changes.

---

## 5. Token Request and Claim Validation

### 5.1 Request Token

> **SENSITIVE — the access token is a bearer credential:**
> Anyone who obtains the token can make API calls on behalf of this client until it expires. Treat it with the same care as the client secret.

First, load credentials from `.env` (see Section 4.2):

```bash
source .env
```

Request a token:

```bash
curl -s --request POST \
  --url "$M2M_AUTH0_DOMAIN/oauth/token" \
  --header 'content-type: application/json' \
  --data "{
    \"client_id\":\"$M2M_CLIENT_ID\",
    \"client_secret\":\"$M2M_CLIENT_SECRET\",
    \"audience\":\"$M2M_AUDIENCE\",
    \"grant_type\":\"client_credentials\"
  }"
```

The command returns JSON (for example: `{"access_token":"...","token_type":"Bearer","expires_in":86400}`).

For scripted use, extract and hold the token in a shell variable — avoid writing it to disk where possible:

```bash
ACCESS_TOKEN=$(curl -s --request POST \
  --url "$M2M_AUTH0_DOMAIN/oauth/token" \
  --header 'content-type: application/json' \
  --data "{
    \"client_id\":\"$M2M_CLIENT_ID\",
    \"client_secret\":\"$M2M_CLIENT_SECRET\",
    \"audience\":\"$M2M_AUDIENCE\",
    \"grant_type\":\"client_credentials\"
  }" | jq -r '.access_token')

if [[ -z "$ACCESS_TOKEN" || "$ACCESS_TOKEN" == "null" ]]; then
  echo "Token retrieval failed"
  exit 1
fi
```

If you must write the token to a file for multi-step testing (use example filenames below — choose any names you like):

```bash
# Example: save to a temporary file (example filename: token.txt)
curl -s --request POST \
  --url "$M2M_AUTH0_DOMAIN/oauth/token" \
  --header 'content-type: application/json' \
  --data "{
    \"client_id\":\"$M2M_CLIENT_ID\",
    \"client_secret\":\"$M2M_CLIENT_SECRET\",
    \"audience\":\"$M2M_AUDIENCE\",
    \"grant_type\":\"client_credentials\"
  }" > token_response.json   # example filename — delete immediately after use

jq -r '.access_token' token_response.json > token.txt   # example filename
chmod 600 token.txt

# Validate
if [[ ! -s token.txt ]] || [[ "$(cat token.txt)" == "null" ]]; then
  echo "Token retrieval failed"
  cat token_response.json
  exit 1
fi

# Delete the full response immediately — it is not needed further
rm -f token_response.json
```

> The filenames `token.txt` and `token_response.json` used here are **examples only**. Use whatever names suit your workflow — but ensure they are in `.gitignore` and deleted after use. Never commit them.

### 5.2 Decode and Verify Claims
```bash
TOKEN=$(cat token.txt | tr -d '\n')
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

If `base64` decoding fails on your shell, use this safe Python fallback:

```bash
python3 - <<'EOF'
import base64, json
token = open("token.txt").read().strip()
payload_part = token.split(".")[1]
payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_part))
print(json.dumps(payload, indent=2))
EOF
```

Required values:
- `iss`: `https://auth.ebl.lmu.de/`
- `aud`: `dictionary-api`
- `gty`: `client-credentials`
- `permissions`: includes `read:bibliography` and `write:bibliography`

Fail fast checks:

```bash
python3 - <<'EOF'
import base64, json, sys
token = open("token.txt").read().strip()
payload_part = token.split(".")[1]
payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_part))

errors = []
if payload.get("iss") != "https://auth.ebl.lmu.de/":
  errors.append("iss mismatch")
if payload.get("aud") != "dictionary-api":
  errors.append("aud mismatch")
if payload.get("gty") != "client-credentials":
  errors.append("gty mismatch")
permissions = payload.get("permissions", [])
if "read:bibliography" not in permissions or "write:bibliography" not in permissions:
  errors.append("missing required permissions")

if errors:
  print("Token validation failed:", ", ".join(errors))
  sys.exit(1)
print("Token validation passed")
EOF
```

---

## 6. Authorization Tests

### 6.1 Read Test (Reference)
```bash
TOKEN=$(cat token.txt | tr -d '\n')
curl -s -o /tmp/read_result.json -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  https://www.ebl.lmu.de/api/bibliography/LS139
cat /tmp/read_result.json
```

Expected:
- HTTP 200

Note:
- This endpoint is public in current behavior and may return 200 without token.

Quick assertion:

```bash
STATUS=$(curl -s -o /tmp/read_result.json -w "%{http_code}" \
  -H "Authorization: Bearer $(cat token.txt | tr -d '\n')" \
  https://www.ebl.lmu.de/api/bibliography/LS139)

[[ "$STATUS" == "200" ]] || { echo "Read test failed (HTTP $STATUS)"; cat /tmp/read_result.json; exit 1; }
echo "Read test passed"
```

### 6.2 Write Test (Local)
```bash
TOKEN=$(cat token.txt | tr -d '\n')
curl -s -o /tmp/write_result.json -w "HTTP %{http_code}\n" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"M2M-TEST-LOCAL","type":"article-journal","title":"M2M Write Test","author":[{"family":"Test","given":"M2M"}],"issued":{"date-parts":[[2026]]}}' \
  http://localhost:8001/bibliography
cat /tmp/write_result.json
```

Expected:
- HTTP 201

Quick assertion:

```bash
STATUS=$(curl -s -o /tmp/write_result.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $(cat token.txt | tr -d '\n')" \
  -H "Content-Type: application/json" \
  -d '{"id":"M2M-TEST-LOCAL","type":"article-journal","title":"M2M Write Test","author":[{"family":"Test","given":"M2M"}],"issued":{"date-parts":[[2026]]}}' \
  http://localhost:8001/bibliography)

[[ "$STATUS" == "201" ]] || { echo "Write test failed (HTTP $STATUS)"; cat /tmp/write_result.json; exit 1; }
echo "Write test passed"
```

Optional cleanup in local Mongo shell if needed:

```javascript
db.getCollection("bibliography").deleteOne({ id: "M2M-TEST-LOCAL" })
```

---

## 7. Negative Permission Test (Required)
1. In Auth0, remove `write:bibliography` from the M2M app (keep `read:bibliography`).
2. Request a new token from `https://auth.ebl.lmu.de/oauth/token`.
3. Save that token to `negative_token.txt` (same extraction pattern as Section 5.1).
4. Decode `negative_token.txt` and confirm claims before testing:
   - `permissions` must NOT contain `write:bibliography`
   - `permissions` should still contain `read:bibliography`
5. Re-run write test with `negative_token.txt`.

Expected:
- HTTP 403

6. Restore `write:bibliography`.
7. Request a fresh token again and verify write returns HTTP 201.

Command for step 4:

```bash
STATUS=$(curl -s -o /tmp/negative_write_result.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $(cat negative_token.txt | tr -d '\n')" \
  -H "Content-Type: application/json" \
  -d '{"id":"M2M-TEST-NEGATIVE","type":"article-journal","title":"Should Fail","author":[{"family":"Test","given":"M2M"}],"issued":{"date-parts":[[2026]]}}' \
  http://localhost:8001/bibliography)

[[ "$STATUS" == "403" ]] || { echo "Negative test failed (HTTP $STATUS)"; cat /tmp/negative_write_result.json; exit 1; }
echo "Negative test passed"
```

Verified result on localhost:
- Fresh token claims contained `read:bibliography` only
- `POST /bibliography` returned `HTTP 403 Forbidden`

---

## 8. Security Rules

### What is sensitive

| Item | Sensitivity | Rule |
|---|---|---|
| `CLIENT_SECRET` | **Critical** | Never log, commit, print, or share. Rotate immediately if exposed. |
| `ACCESS_TOKEN` (JWT) | **High** | Bearer credential — treat as a password. Never commit or paste into issues/PRs. |
| `CLIENT_ID` | Medium | Not secret alone, but do not publish unnecessarily. |
| Auth0 domain, audience, API URLs | Low / Public | Non-secret reference values. |

### Rules
- Store `CLIENT_ID` and `CLIENT_SECRET` in `.env` (or a secrets manager). Add `.env` to `.gitignore`.
- Never write secrets or tokens into scripts, config files, or code that is committed.
- Never paste a `CLIENT_SECRET` or `ACCESS_TOKEN` into a GitHub issue, PR comment, chat message, or email.
- Delete any temporary token files immediately after use. Do not leave them on disk.
- Use partner-specific M2M applications — never share credentials across partners.
- Rotate the `CLIENT_SECRET` immediately if exposure is suspected. Revoke existing tokens by rotating.
- Prefer keeping tokens in shell variables (`ACCESS_TOKEN=$(...)`) over writing them to files.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| HTTP 403 on write with token | Token missing `write:bibliography` OR token validated as guest | Verify permissions and claim set; request fresh token |
| Token has wrong `iss` | Token requested from native tenant domain | Request token from `https://auth.ebl.lmu.de/oauth/token` |
| JWT rejected (`InvalidIssuerError`) | `iss` does not match API `AUTH0_ISSUER` | Use matching custom domain and re-issue token |
| Write still fails locally after code change | API process still running old code | Restart local API process and retry |

---

## 10. Backend Implementation Notes (Already Applied)
The API authentication backend was updated to support M2M tokens correctly:
- Removed non-standard required claim `openid`
- Added M2M path (`gty=client-credentials`) that skips `/userinfo`

This avoids guest fallback for valid M2M tokens.

---

## 11. Completion Checklist
- [x] M2M app created/verified
- [x] API authorization configured
- [x] Required bibliography permissions enabled
- [x] Token from correct custom domain validated
- [x] Local write test passes (HTTP 201)
- [x] Negative permission test completed (403 without `write:bibliography`)
- [ ] Production deployment completed
- [ ] Production write validation completed
