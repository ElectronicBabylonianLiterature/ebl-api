# TASK-3: ebl-frontend – Auto-create `.env.local` and inject Codespaces secrets

Mirrors the implementation from `ebl-api` PR #717 (`fix-devcontainer`) in the
[ebl-frontend](https://github.com/ElectronicBabylonianLiterature/ebl-frontend) repository.

## Context

The `ebl-api` devcontainer crashed on a clean clone because `runArgs: ["--env-file", ".env"]`
failed when `.env` was absent (gitignored). The fix added `initializeCommand` → `init.sh` to
auto-create `.env` and inject Codespaces secrets before the container builds.

The frontend devcontainer does **not** use `--env-file` in `runArgs`, so there is no crash risk.
However, without `.env.local`, `yarn start` starts with empty env vars and the app won't connect
to the API or Auth0. Applying the same pattern gives a consistent, zero-friction Codespaces
experience across both repositories.

Key differences from ebl-api:
| | ebl-api | ebl-frontend |
|---|---|---|
| Env file | `.env` | `.env.local` |
| Example file | `.env.example` (exists) | `.env.test` (already exists) |
| devcontainer base | `universal:2` image | Custom `Dockerfile` (node:20) |
| `runArgs` crash risk | Yes (was the root cause) | No |
| Python 3 on Codespaces host | Yes | Yes (same host) |

---

## Checklist

- [ ] Verify `.env.local` is in `.gitignore`
- [ ] Create `.devcontainer/init.sh`
- [ ] Modify `.devcontainer/devcontainer.json` – add `initializeCommand`
- [ ] Update root `README.md` – step 6 in Option 1 (Codespaces)
- [ ] Register `.env.local` values as Codespaces secrets (see §5)
- [ ] Smoke-test in a fresh Codespace
- [ ] Remove this file before merging the PR

---

## 1. Verify `.env.local` is gitignored

`.env.test` already exists and will be used as the template for `.env.local`. No new
example file needs to be created.

Verify `.env.local` is covered in `.gitignore` (Create React App adds it by default):

```sh
grep '\.env\.local' .gitignore
# Expected output: .env.local
# If missing, add it manually.
```

---

## 2. Create `.devcontainer/init.sh`

Create `.devcontainer/init.sh` with the following content. The logic is identical to the
ebl-api version (`ebl-api/.devcontainer/init.sh`) with the target file changed from `.env`
to `.env.local` and the template file changed from `.env.example` to `.env.test`.

```bash
#!/bin/bash
set -e

# Create .env.local from .env.test if it doesn't exist
test -f .env.local || cp .env.test .env.local

# For each variable defined in .env.test, if a Codespaces secret with the
# same name is available in the host environment, override the placeholder value.
python3 << 'PYEOF'
import os
import re

with open('.env.test') as f:
    keys = [
        line.split('=')[0].strip()
        for line in f
        if line.strip() and not line.startswith('#')
    ]

with open('.env.local') as f:
    content = f.read()

injected = []
for key in keys:
    value = os.environ.get(key, '')
    if value:
        content = re.sub(
            r'^' + re.escape(key) + r'=.*',
            key + '=' + value,
            content,
            flags=re.MULTILINE
        )
        injected.append(key)

if injected:
    with open('.env.local', 'w') as f:
        f.write(content)
    print('Injected Codespaces secrets into .env.local: ' + ', '.join(injected))
else:
    print('No Codespaces secrets found — .env.local uses placeholder values from .env.test')
PYEOF
```

Make the script executable:

```sh
chmod +x .devcontainer/init.sh
```

---

## 3. Modify `.devcontainer/devcontainer.json`

Add `"initializeCommand"` as the **first** new key, immediately before `"postCreateCommand"`.

**Current `devcontainer.json`:**
```json
{
  "name": "EBL Frontend",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "features": {
    "ghcr.io/devcontainers/features/git-lfs:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "esbenp.prettier-vscode",
        "davidanson.vscode-markdownlint",
        "dbaeumer.vscode-eslint",
        "syler.sass-indented"
      ]
    }
  },
  "postCreateCommand": "git config --global core.autocrlf input && git config --global core.eol lf && git config --global core.safecrlf true && yarn install",
  "forwardPorts": [3000],
  "portsAttributes": {
    "3000": {
      "label": "Application",
      "onAutoForward": "openBrowser"
    }
  }
}
```

**Updated `devcontainer.json`** (add the `initializeCommand` line):
```json
{
  "name": "EBL Frontend",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "features": {
    "ghcr.io/devcontainers/features/git-lfs:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "esbenp.prettier-vscode",
        "davidanson.vscode-markdownlint",
        "dbaeumer.vscode-eslint",
        "syler.sass-indented"
      ]
    }
  },
  "initializeCommand": "bash .devcontainer/init.sh",
  "postCreateCommand": "git config --global core.autocrlf input && git config --global core.eol lf && git config --global core.safecrlf true && yarn install",
  "forwardPorts": [3000],
  "portsAttributes": {
    "3000": {
      "label": "Application",
      "onAutoForward": "openBrowser"
    }
  }
}
```

**Why `initializeCommand`?**
`initializeCommand` runs on the Codespaces host *before* `docker build` and `docker run`. This
guarantees `.env.local` exists and is populated with secrets before the container starts and
before `postCreateCommand` (`yarn install`) runs.

---

## 4. Update `README.md` (root)

In the **"Option 1: GitHub Codespaces with Dev Containers"** section, step 6 currently says:

> 6. Configure the required environment variables in `.env.local`
>    (see [Running the application](#running-the-application) section)

Replace step 6 with the following (and optionally renumber or adjust surrounding steps):

```markdown
6. `.env.local` is created automatically from `.env.test` before the container
   builds. If you have configured [Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces)
   with the same names as the keys in `.env.test`, they are injected into
   `.env.local` automatically and the app will be fully configured on first start.
   Otherwise, open `.env.local` inside the container and fill in your credentials
   (see [Running the application](#running-the-application) section), then run
   `yarn start` to restart the dev server.
```

---

## 5. Create `.devcontainer/README.md` (optional but recommended)

The frontend devcontainer currently has no README. Create `.devcontainer/README.md`:

```markdown
# Dev Container Configuration

This directory contains the development container configuration for the EBL Frontend project.

## Files

- `devcontainer.json` – Main dev container configuration
- `Dockerfile` – Container image definition (Node 20 + ggshield)
- `README.md` – This file

## Environment Variables

The project reads configuration from `.env.local` at the repository root. This file is
gitignored (Create React App convention) and must not be committed.

### Setup

1. **Automatic Setup**: Before the container is created, `initializeCommand` runs
   `.devcontainer/init.sh` on the host. This script:
   - Creates `.env.local` from `.env.test` if `.env.local` does not already exist.
   - For each key defined in `.env.test`, if a [Codespaces secret](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces)
     with the same name is available in the host environment, its value is written into
     `.env.local`, replacing the placeholder.

2. **Update Values**: Edit `.env.local` with your actual credentials for:
   - Auth0 configuration (domain, client ID, audience)
   - eBL API URL
   - Sentry DSN
   - Contact emails
   - Google Analytics tracking ID
   - GitGuardian API key (for pre-commit secret scanning)

### Security

- ✅ `.env.local` is in `.gitignore` and will never be committed
- ✅ `.env.test` contains only placeholder values and is committed to the repository
- ⚠️ Never commit actual credentials to version control
```

---

## 6. Register `.env.local` values as Codespaces secrets

Run the following from inside your ebl-frontend local clone (or from any machine that has
your `.env.local` populated with real credentials and the `gh` CLI authenticated).

```sh
# Authenticate gh CLI if not already
gh auth status   # must show a logged-in account

# Register all key=value pairs from .env.local as user-level Codespaces secrets
# scoped exclusively to the ebl-frontend repo
gh secret set \
  --app codespaces \
  --user \
  --env-file .env.local \
  --repos ElectronicBabylonianLiterature/ebl-frontend
```

This will encrypt and upload each secret individually. Output will list each secret name
as it is set. After this, any new Codespace created on ebl-frontend will have these
secrets available as environment variables on the Codespaces host when `init.sh` runs.

> **Tip:** The same command can be re-run at any time to update secret values. To verify
> which secrets are registered:
> ```sh
> gh secret list --app codespaces --user
> ```

### Secrets that will be registered

| Secret name | Description |
|---|---|
| `REACT_APP_AUTH0_DOMAIN` | Auth0 tenant domain |
| `REACT_APP_AUTH0_CLIENT_ID` | Auth0 SPA client ID |
| `REACT_APP_AUTH0_AUDIENCE` | Auth0 API audience identifier |
| `REACT_APP_DICTIONARY_API_URL` | eBL API base URL |
| `REACT_APP_SENTRY_DSN` | Sentry DSN for error tracking |
| `REACT_APP_CORRECTIONS_EMAIL` | Contact email for corrections |
| `REACT_APP_INFO_EMAIL` | General contact email |
| `REACT_APP_GA_TRACKING_ID` | Google Analytics 4 measurement ID |
| `GITGUARDIAN_API_KEY` | GitGuardian key for pre-commit secret scan |

---

## 7. Verification

After creating a new Codespace on the branch:

1. In the Codespaces creation log, look for the `initializeCommand` step output:
   ```
   Injected Codespaces secrets into .env.local: REACT_APP_AUTH0_DOMAIN, ...
   ```
   or, if no secrets are registered:
   ```
   No Codespaces secrets found — .env.local uses placeholder values from .env.test
   ```
   ```

2. Inside the container, verify `.env.local` was created and contains the expected values:
   ```sh
   cat .env.local
   ```

3. Run `yarn start` and confirm the app loads and connects to the API / Auth0 successfully.

---

## Reference

- ebl-api implementation: PR #717 (`fix-devcontainer` branch), commit `81fadd2a`
- ebl-api `init.sh`: `.devcontainer/init.sh`
- GitHub Codespaces secrets docs: https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces
