---
applyTo: '**'
---

Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

## Scope and Project Context

- This is a backend Python API project. Use backend-appropriate patterns, architecture, and tooling.
- Do not make any changes to the codebase unless explicitly requested.

## Coding Standards

- Follow the existing coding style and conventions used in the project.
- Always use full variable and function names for clarity.
- Ensure that all functions and methods have appropriate type hints. Avoid using `Any` unless very necessary.
- Functions should be small and focused on a single task.
- Refactor long and complex code automatically.
- Do not add comments to the code unless explicitly requested.

## Commands and Tooling

- When running shell commands for project tasks, always use `poetry run` unless using `task`.

## Testing and Quality

- Add / update tests for any new functionality or significant changes.
- When writing tests, ensure they are isolated and do not depend on external state (Jest + React Testing Library conventions).
- Ensure that coverage is 100% after changes in affected code.
- Never remove, disable, skip, or comment out existing tests without explicit user confirmation.
- Only propose removing a test when the underlying code path was removed or changed such that the assertion is no longer meaningful.
- If test removal is proposed, provide detailed justification first and wait for explicit user approval before making that change.

## Task Tracking and Cleanup

- For every task, create a mandatory detailed TODO list in a `.md` file.
- For every task, create and maintain a detailed work log in a `.md` file.
- Use a consistent naming convention for these files: `TASK-<id>-todo.md` and `TASK-<id>-log.md`.
- Keep both the task TODO list and task log constantly updated while working.
- Before a PR is merged, check for these task TODO/log `.md` files and remind to remove them.

## Review Guidelines

- Keep review comments short, specific, and actionable.
- Prioritize correctness, regressions, security, and test coverage in every review.
- Verify changed behavior locally by running the modified backend service and related tests before finalizing review conclusions.
- Export every detailed review to a `.md` file using the same convention: `TASK-<id>-review.md`.
- Use a consistent review template with these sections: `Summary`, `Findings`, `Severity`, `Reproduction Steps`, and `Recommendation`.
- Keep the review file updated as findings change, and remind to remove it before a PR is merged.