# TASK-2 LOG — Fix devcontainer initializeCommand

## Problem
`runArgs: ["--env-file", ".env"]` in `devcontainer.json` causes container creation to fail on
every fresh Codespace because `.env` is gitignored and absent on a clean clone. Docker rejects
`docker run --env-file .env` when the file does not exist, leaving a broken fallback container
without the `codespace` user. Two incidents confirmed (10:36 and 12:01 UTC 2026-05-26, both
from codespace `verbose-capybara` on `master`).

Root cause documented in `.devcontainer/TROUBLESHOOTING.md`.

## Solution chosen
Option A: `initializeCommand` pointing to `.devcontainer/init.sh`.
`initializeCommand` runs on the Codespaces host *before* `docker run`, so `.env` always exists
when `--env-file .env` is processed. The script also injects any matching Codespaces secrets.

## Changes

### 2026-05-26
- Created TASK-2-todo.md and TASK-2-log.md
- Created `.devcontainer/init.sh`: creates `.env` from `.env.example` if absent, then iterates
  keys in `.env.example` and overwrites placeholders with any matching Codespaces secrets found
  in the host environment
- Updated `devcontainer.json`: `initializeCommand` changed from one-liner to `bash .devcontainer/init.sh`
- Updated `.devcontainer/README.md`: removed false "Automatic Setup" claim, documented
  `initializeCommand` + secret injection behaviour
- Updated `.devcontainer/TROUBLESHOOTING.md`: corrected prebuild hypothesis, added correct root
  cause analysis (missing `.env` + `--env-file` failure), updated Option A description
- Validated JSON (`python3 -m json.tool`) and shell syntax (`bash -n`)
- Smoke-tested `init.sh` with fake env vars and special characters — passed
- Registered all 11 `.env` variables as user-level Codespaces secrets scoped to
  `ElectronicBabylonianLiterature/ebl-api` via `gh secret set --app codespaces --user --env-file .env --repos ...`
- Deleted old `fix-devcontainer` branch (was based on `add-realia`), recreated from `master`
