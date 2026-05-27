# TASK-2 LOG — Fix devcontainer initializeCommand

## Problem

`runArgs: ["--env-file", ".env"]` in `devcontainer.json` causes container
creation to fail on every fresh codespace because `.env` is gitignored and
absent on a clean clone. Docker rejects `docker run --env-file .env` when
the file does not exist, leaving a broken fallback container without the
`codespace` user. Two incidents confirmed (10:36 and 12:01 UTC 2026-05-26,
both from codespace `verbose-capybara` on `master`).

Root cause documented in `.devcontainer/TROUBLESHOOTING.md`.

## Solution chosen

Option A: `initializeCommand` pointing to `.devcontainer/init.sh`.
`initializeCommand` runs on the Codespaces host *before* `docker run`, so
`.env` always exists when `--env-file .env` is processed. The script also
injects any matching Codespaces secrets.

## Changes

### 2026-05-26

- Created TASK-2-todo.md and TASK-2-log.md
- Created `.devcontainer/init.sh`: creates `.env` from `.env.example` if
  absent, then iterates keys in `.env.example` and overwrites placeholders
  with any matching Codespaces secrets found in the host environment
- Updated `devcontainer.json`: `initializeCommand` changed from one-liner
  to `bash .devcontainer/init.sh`
- Updated `.devcontainer/README.md`: removed false "Automatic Setup" claim,
  documented `initializeCommand` + secret injection behaviour
- Updated `.devcontainer/TROUBLESHOOTING.md`: corrected prebuild hypothesis,
  added correct root cause analysis (missing `.env` + `--env-file` failure),
  updated Option A description
- Validated JSON (`python3 -m json.tool`) and shell syntax (`bash -n`)
- Smoke-tested `init.sh` with fake env vars and special characters — passed
- Registered all 11 `.env` variables as user-level Codespaces secrets
  scoped to `ElectronicBabylonianLiterature/ebl-api` via
  `gh secret set --app codespaces --user --env-file .env --repos ...`
- Deleted old `fix-devcontainer` branch (was based on `add-realia`),
  recreated from `master`

### 2026-05-27 (Session 2 — Sourcery AI fixes + markdownlint)

- Applied Sourcery AI Issue #1 fix: replaced `key + '=' + value` with
  `lambda m: f'{key}={value}'` in `re.sub()` call in `init.sh` to prevent
  backslash/backreference corruption of secret values
- Applied Sourcery AI Issue #2 fix: replaced `if value:` with
  `if key in os.environ:` to correctly handle secrets explicitly set to
  empty string (instead of skipping them)
- Applied Sourcery AI Issue #3 fix: corrected "Codespace" → "codespace"
  in TASK-2-log.md line 5
- Deleted the unauthorized `.markdownlint.json` that was disabling MD013,
  MD041, MD060; recreated `.markdownlintignore` to exclude only
  `.venv/` and `.pytest_cache/` (legitimate — do not lint vendored code)
- Added `lint-md` task to Taskfile and included it in `test-all`
- Updated copilot instructions: added H1 heading (MD041 fix), wrapped
  all long lines (MD013), added markdownlint gate rule and explicit
  prohibition on modifying linting configs without user approval
- Fixed MD013/MD060/MD041 across all project markdown files by wrapping
  prose, fixing table spacing, and adding headings where required
- All quality gates re-verified: `bash -n init.sh` PASS,
  `task test-secrets` 4/4 PASS
