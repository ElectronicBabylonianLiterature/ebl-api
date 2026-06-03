# Dev Container Configuration

This directory contains the development container configuration for the
EBL API project.

## Files

- `devcontainer.json` - Main dev container configuration
- `setup.sh` - Post-create setup script that installs dependencies
- `inject-secrets.py` - Post-create script that injects Codespaces secrets
  and syncs missing keys
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
   - **After container build** (`postCreateCommand`): Runs
     `inject-secrets.py` inside the container. This script:
     - Injects any
       [Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces)
       whose names match keys in `.env.example`, but only if the current
       `.env` value still matches the placeholder (user-edited values are
       preserved on rebuild).
     - Appends any keys present in `.env.example` but missing from `.env`,
       keeping your environment in sync when new variables are introduced.

2. **Update Values**: Edit `.env` with your actual credentials for:
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

No manual steps are required - everything works automatically after container rebuild.

### Security

- ✅ `.env` is in `.gitignore` and will never be committed
- ✅ `.env.example` contains only placeholder values and is committed to the repository
- ⚠️ Never commit actual credentials to version control

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
