---
applyTo: '**'
---

# Copilot Instructions

Provide project context and coding guidelines that AI should follow when
generating code, answering questions, or reviewing changes.

## Scope and Project Context

- This is a backend Python API project. Use backend-appropriate patterns,
  architecture, and tooling.
- Do not make any changes to the codebase unless explicitly requested.

## API Contract Authority

- The backend API schema is the source of truth for request and response
  field names.
- When a client/backend field naming mismatch exists, align the client to
  the backend schema by default.
- Do not introduce backend aliases for alternate client field names unless
  explicitly requested as a backward-compatibility requirement.

## Coding Standards

- Follow the existing coding style and conventions used in the project.
- Always use full variable and function names for clarity.
- Ensure that all functions and methods have appropriate type hints.
  Avoid using `Any` unless very necessary.
- Functions should be small and focused on a single task.
- Refactor long and complex code automatically.
- Do not add comments to the code unless explicitly requested.
- HARD GATE: no `*.py` file may exceed 250 total lines. If a change pushes a
  file past this limit, refactor by extracting modules or splitting test files
  before completing the task. This is non-negotiable and applies to both
  source and test files.

## Commands and Tooling

- When running shell commands for project tasks, always use `poetry run`
  unless using `task`.

## Pre-Commit Hard Gates (mandatory before every commit)

Run all of the following in order and confirm each passes before committing:

1. `task format` — auto-format code (must exit 0 with no unstaged changes left)
2. `task test` — full test suite (must pass with 0 failures)
3. `poetry run pytest <changed modules> --cov=<changed modules>
   --cov-report=term-missing` — 100% coverage on all changed files
4. `poetry run flake8 <changed modules> --max-line-length=120` — zero lint
   errors
5. `poetry run mypy <changed modules> --ignore-missing-imports` — zero type
   errors (pre-existing errors are not acceptable; fix them)
6. `npx pyright <changed files>` — zero Pylance/Pyright errors. Pylance uses
   the Pyright engine, and `pyrightconfig.json` at the repo root pins the
   interpreter (`.venv`) and `typeCheckingMode`, so the CLI reproduces exactly
   what the IDE reports. Pass no flags — the config supplies them. Run it
   against every file the change touches. All errors must be addressed,
   including ones that pre-existed in a touched file; "it was already broken"
   is not an acceptable justification. Prefer real fixes (typed converter and
   validator functions instead of the `attr.ib` decorator form, `typing.cast`
   for values marshmallow types as `Any`, mapping-style access such as
   `req.context["user"]` for Falcon's dynamic `Context`) over suppression
   comments. This is non-negotiable.

   Never "fix" a Pyright error by loosening `pyrightconfig.json`. If the IDE
   reports `Unknown`/`partially unknown` types en masse (e.g. `list[Unknown]`),
   the interpreter is not resolving — check that VS Code's selected interpreter
   is `.venv`, not the system Python. Do not raise `typeCheckingMode` to
   `strict`: `marshmallow`, `attrs`, `pydash` and `factory_boy` ship no type
   information, so strict reports ~24k `Unknown` cascades across the codebase.

Never commit if any gate fails or was skipped.

## Testing and Quality

- Add / update tests for any new functionality or significant changes.
- When writing tests, ensure they are isolated and do not depend on
  external state (pytest conventions).
- Ensure that coverage is 100% after changes in affected code.
- HARD GATE: pre-existing coverage gaps must be filled, not preserved. Any
  line you add, modify, move, or relocate must end at 100% coverage, even if
  it was uncovered before you touched it. "It was already uncovered on the
  base branch" is not an acceptable justification for leaving a touched line
  uncovered — add the missing tests as part of the change. This is
  non-negotiable.
- Never remove, disable, skip, or comment out existing tests without
  explicit user confirmation.
- Only propose removing a test when the underlying code path was removed
  or changed such that the assertion is no longer meaningful.
- If test removal is proposed, provide detailed justification first and
  wait for explicit user approval before making that change.
- Run `task lint-md` as a quality gate; zero errors and warnings are
  required before committing any markdown changes.
- Never modify linting or formatting configuration files
  (`.markdownlint.json`, `.markdownlintignore`, `pyproject.toml` linting
  sections, `mypy.ini`, `ruff.toml`, etc.) without an explicit user
  request. Fix real content issues instead of disabling rules.

## Task Tracking and Cleanup

- For every task, create a mandatory detailed TODO list in a `.md` file.
- For every task, create and maintain a detailed work log in a `.md`
  file.
- Use a consistent naming convention for these files:
  `TASK-<id>-todo.md` and `TASK-<id>-log.md`.
- Keep both the task TODO list and task log constantly updated while
  working.
- Before a PR is merged, check for these task TODO/log `.md` files and
  remind to remove them.

## Review Guidelines

- HARD GATE: before finalizing any PR review, fetch and incorporate all
  existing GitHub feedback on the PR — submitted reviews, inline (diff)
  review comments, and issue/conversation comments — including from bots
  (e.g. Sourcery, qlty, Codex). Also fetch feedback for any PR whose branch
  has been merged into the one under review. Use the GitHub CLI, e.g.:
  `gh api repos/<owner>/<repo>/pulls/<n>/reviews`,
  `gh api repos/<owner>/<repo>/pulls/<n>/comments`, and
  `gh api repos/<owner>/<repo>/issues/<n>/comments`. Every unresolved finding
  must be explicitly addressed or acknowledged with a rationale in the review
  file. A review that ignores existing PR feedback is incomplete and must not
  be finalized. This is non-negotiable.
- Keep review comments short, specific, and actionable.
- Prioritize correctness, regressions, security, and test coverage in
  every review.
- Verify changed behavior locally by running the modified backend service
  and related tests before finalizing review conclusions.
- Export every detailed review to a `.md` file using the same
  convention: `TASK-<id>-review.md`.
- Use a consistent review template with these sections: `Summary`,
  `Findings`, `Severity`, `Reproduction Steps`, and `Recommendation`.
- Keep the review file updated as findings change, and remind to remove
  it before a PR is merged.
