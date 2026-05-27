# TASK-4 LOG — Address PR #717 Review Comments

## Overview

Addressing unresolved review comments from Sourcery AI and GitHub Copilot
on PR #717 (`fix-devcontainer`).

## Issues to Address

| # | Reviewer | File | Issue |
| --- | --- | --- | --- |
| 1 | Copilot | `Taskfile.dist.yml:37` | `lint:` task is a no-op (regression) |
| 2 | Copilot | `init.sh:33` | Newlines in secret values corrupt `.env` |
| 3 | Copilot | `.devcontainer/init.sh:6` | Dead `.env` fallback in `setup.sh` |
| 4 | Copilot | `.devcontainer/init.sh:9` | Host prereqs not documented |
| 5 | Copilot | `.devcontainer/README.md:62` | Wrong feature source path |
| 6 | Copilot | `Taskfile.dist.yml:35` | `npx` version unpinned |

## Work Log

### 2026-05-27

- Fixed `lint:` task regression in `Taskfile.dist.yml`
  — restored `poetry run ruff check ebl {{.CLI_ARGS}}`
- Pinned `markdownlint-cli2@0.22.1` in `Taskfile.dist.yml` lint-md command
- Stripped `\r`/`\n` from secret values in `.devcontainer/init.sh`
  before regex substitution to prevent `.env` corruption
- Removed dead `.env` bootstrap block from `.devcontainer/setup.sh`
  (lines ~75-82); `initializeCommand` now sole source of truth
- Added host prerequisites note to `.devcontainer/README.md`
  (bash + python3 required; not available on Windows without WSL)
- Fixed feature source paths in `.devcontainer/README.md`
  (`devcontainers-contrib` → `devcontainers-extra`, matching `devcontainer.json`)
- `task lint-md` gate: **0 errors** ✅
