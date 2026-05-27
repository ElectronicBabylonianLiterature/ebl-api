# TASK-4 TODO — Address PR #717 Review Comments

Source: Sourcery AI + GitHub Copilot reviews on PR #717

## Open Items

- [x] Fix `lint:` task regression in `Taskfile.dist.yml` (no-op, ruff check removed)
- [x] Strip newlines from secret values in `.devcontainer/init.sh` before injection
- [x] Remove dead `.env` bootstrap block from `.devcontainer/setup.sh`
- [x] Document `initializeCommand` host prerequisites (bash, python3) in `.devcontainer/README.md`
- [x] Fix incorrect feature source paths in `.devcontainer/README.md`
  (`devcontainers-contrib` → `devcontainers-extra`)
- [x] Pin `markdownlint-cli2` version in `Taskfile.dist.yml` lint-md command

## Resolved (Already Addressed in Earlier Commits)

- [x] `re.sub` backslash/group-reference bug — fixed with `lambda m:` replacement
- [x] `if value:` skips empty secrets — fixed with `if key in os.environ:`
- [x] Capitalization of "codespace" in TASK-2-log.md — fixed (outdated)

## Quality Gates

- [x] `task lint-md` — 0 errors
- [x] Manually review `.devcontainer/init.sh` Python block
