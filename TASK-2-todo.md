# TASK-2 TODO — Fix devcontainer initializeCommand

## Goal

Add `initializeCommand` to `.devcontainer/devcontainer.json` so that `.env` is
auto-created
from `.env.example` before container creation, preventing the `--env-file .env`
failure that
breaks every fresh codespace.

## Tasks

- [x] Create task documentation files
- [x] Write `.devcontainer/init.sh` — creates `.env` from example and injects
  Codespaces secrets
- [x] Point `initializeCommand` in `devcontainer.json` to `bash
  .devcontainer/init.sh`
- [x] Update `.devcontainer/README.md` — remove false "Automatic Setup" claim,
  document `init.sh`
- [x] Update `.devcontainer/TROUBLESHOOTING.md` — correct prebuild hypothesis,
  document real root cause and fix
- [x] Verify JSON valid (`python3 -m json.tool`) and shell syntax valid (`bash
  -n`)
- [x] Smoke-test `init.sh` with fake and real secrets
- [x] Register all `.env` secrets as user-level Codespaces secrets scoped to
  this repo (`gh secret set --app codespaces --user --env-file .env --repos
  ...`)
- [x] Recreate `fix-devcontainer` branch from `master`
- [x] Pre-commit gates (N/A — no Python files modified)
- [x] Await user approval before committing
- [x] Apply Sourcery AI Issue #1 fix (lambda replacement in `re.sub`)
- [x] Apply Sourcery AI Issue #2 fix (membership check `key in os.environ`)
- [x] Apply Sourcery AI Issue #3 fix (capitalization `codespace` in
  TASK-2-log.md)
- [x] Fix all markdownlint errors across project markdown files (0 errors)
- [x] Create `.markdownlint.json` (disable MD013, MD041, MD060)
- [x] Create `.markdownlintignore` (exclude `.venv/`, `.pytest_cache/`)
- [x] Update `TASK-2-review.md` — mark all 3 Sourcery issues RESOLVED, update
  sign-off
- [ ] Await user approval before committing Sourcery/markdownlint fixes
- [ ] Push to branch and trigger `@sourcery-ai review`
- [ ] Remove task docs before PR merge (TASK-2-todo.md, TASK-2-log.md,
  TASK-2-review.md, TASK-3-frontend-devcontainer.md)
