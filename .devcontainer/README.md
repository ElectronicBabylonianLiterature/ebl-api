# Dev Container Configuration

This directory contains the development container configuration for the EBL API project.

## Files

- `devcontainer.json` - Main dev container configuration
- `setup.sh` - Post-create setup script that installs dependencies
- `README.md` - This file

## Environment Variables

The project requires environment variables to be configured in a `.env` file at the root of the repository.

### Setup

1. **Automatic Setup**: When the dev container is created, if `.env` doesn't exist, it will be automatically created from `.env.example` with placeholder values.

2. **Manual Setup**: Copy `.env.example` to `.env` and update with your actual credentials:
   ```bash
   cp .env.example .env
   ```

3. **Update Values**: Edit `.env` with your actual credentials for:
   - Auth0 configuration (audience, issuer, PEM certificate)
   - MongoDB connection URI and database name
   - Sentry DSN
   - AI API endpoint

### Security

- ✅ `.env` is in `.gitignore` and will never be committed
- ✅ `.env.example` contains only placeholder values and is committed to the repository
- ⚠️ Never commit actual credentials to version control

## What Gets Installed

### Via Dev Container Features
1. **Poetry** - Python dependency management (installed via `ghcr.io/devcontainers-contrib/features/poetry:2`)
2. **go-task** - Task runner (installed via `ghcr.io/devcontainers-contrib/features/go-task:1`)

### Via setup.sh Script
1. **MongoDB 4.4** - Database server
2. **Rust** - Required for building libcst (pyre-check dependency)
3. **Python dependencies** - All project dependencies via `poetry install --no-root --with dev`

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
