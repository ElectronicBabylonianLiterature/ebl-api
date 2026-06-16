# Dev Container Configuration

This directory contains the development container configuration for the
EBL API project.

## Files

- `devcontainer.json` - Main dev container configuration
- `setup.sh` - Post-create setup script that installs dependencies
- `sync-env.py` - Post-create script that syncs missing keys from
  `.env.example` into `.env`
- `README.md` - This file

## Environment Variables

The project requires environment variables to be configured in a `.env`
file at the root of the repository.

### Setup

1. **Automatic Setup**: Environment configuration happens in two phases:
   - **Before container build** (`initializeCommand`): Creates `.env` from
     `.env.example` if it does not already exist. This step uses only POSIX
     `sh` and works on all host platforms (Linux, macOS, Windows with Git
     Bash or WSL, Codespaces). No bash or Python required on the host.
   - **After container build** (`postCreateCommand`): Runs `sync-env.py`
     inside the container. This script appends any keys present in
     `.env.example` but missing from `.env`, keeping your environment in
     sync when new variables are introduced.

2. **Codespaces Secrets**: When using GitHub Codespaces, configure your
   secrets in
   [Codespaces settings](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces).
   Codespaces automatically injects matching secrets as environment
   variables inside the container — no manual steps or file writes are
   needed. The `.env` file holds placeholder values only; live secrets
   reach the application through the process environment.

3. **Update Values**: Edit `.env` with your actual credentials for local
   (non-Codespaces) development:
   - Auth0 configuration (audience, issuer, PEM certificate)
   - MongoDB connection URI and database name
   - Sentry DSN
   - AI API endpoint

### How Environment Variables are Loaded

Environment variables from `.env` are automatically loaded into the
container via the `runArgs: ["--env-file", ".env"]` configuration in
`devcontainer.json`. This makes them available to all processes,
including:

- Shell sessions
- `poetry run` commands
- `task` commands
- Any other processes running in the container

No manual steps are required - everything works automatically after
container rebuild.

### How it works (two-layer env mechanism)

`.env` must exist and contain every key that the application reads
(placeholder values are fine). Docker will fail at startup if the file
is absent because `--env-file` is unconditional.

`sync-env.py` ensures `.env` always has all keys by appending any that
are present in `.env.example` but not yet in `.env`. This keeps the
file complete when new variables are introduced.

In **Codespaces**, real secret values reach the container through a
separate path:

1. Codespaces passes `--secrets-file` to the Docker CLI when creating
   the container.
2. The devcontainer CLI translates each secret into an explicit
   `-e KEY=value` flag.
3. Docker applies explicit `-e` flags **after** `--env-file`, so they
   override the placeholder values from `.env`.

The result: every key is present in the process environment (from
`.env`), and every key that has a Codespaces secret configured receives
its real value — without writing it to disk.

In **local** (non-Codespaces) development, step 1-3 do not apply.
Edit `.env` directly with your actual credentials.

### Security

- `.env` is in `.gitignore` and will never be committed
- `.env.example` contains only placeholder values and is committed to
  the repository
- Codespaces secrets are injected as process environment variables by
  the platform — they are never written to disk by this project
- Never commit actual credentials to version control

## What Gets Installed

### Via Dev Container Features

1. **Python 3.11** - Runtime for local development
2. **Poetry** - Python dependency management
   (installed via `ghcr.io/devcontainers-extra/features/poetry:2`)
3. **go-task** - Task runner
   (installed via `ghcr.io/devcontainers-extra/features/go-task:1`)

### Via setup.sh Script

1. **MongoDB 4.4** - Database server
2. **Rust** - Required for building libcst (pyre-check dependency)
3. **Python dependencies** - All project dependencies via
   `poetry install --no-root --with dev`

## MongoDB

MongoDB is automatically started on container start via `postStartCommand`:

- Data directory: `/workspaces/data`
- Bind address: `127.0.0.1`
- Port: `27017` (default)
- Log file: `/workspaces/data/mongodb.log`

## Port Forwarding

- Port `8000` - API server (configured but not auto-forwarded)

## VS Code Extensions

The following extensions are automatically installed:

- Python (ms-python.python)
- MongoDB for VS Code (mongodb.mongodb-vscode)
- Markdown Lint (davidanson.vscode-markdownlint)
- Docker (ms-azuretools.vscode-docker)
- Ruff (charliermarsh.ruff)
