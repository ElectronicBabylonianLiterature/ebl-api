# TASK-2 TODO — Fix devcontainer initializeCommand

## Goal
Add `initializeCommand` to `.devcontainer/devcontainer.json` so that `.env` is auto-created
from `.env.example` before container creation, preventing the `--env-file .env` failure that
breaks every fresh codespace.

## Tasks

- [x] Create task documentation files
- [x] Write `.devcontainer/init.sh` — creates `.env` from example and injects Codespaces secrets
- [x] Point `initializeCommand` in `devcontainer.json` to `bash .devcontainer/init.sh`
- [x] Update `.devcontainer/README.md` — remove false "Automatic Setup" claim, document `init.sh`
- [x] Update `.devcontainer/TROUBLESHOOTING.md` — correct prebuild hypothesis, document real root cause and fix
- [x] Verify JSON valid (`python3 -m json.tool`) and shell syntax valid (`bash -n`)
- [x] Smoke-test `init.sh` with fake and real secrets
- [x] Register all `.env` secrets as user-level Codespaces secrets scoped to this repo (`gh secret set --app codespaces --user --env-file .env --repos ...`)
- [x] Recreate `fix-devcontainer` branch from `master`
- [ ] Pre-commit gates (N/A — no Python files modified)
- [ ] Await user approval before committing
