---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

- Do not make any changes to the codebase unless explicitly requested.
- Follow the existing coding style and conventions used in the project.
- Always use full variable and function names for clarity.
- Ensure that all functions and methods have appropriate type hints.
- Do not add comments to the code unless explicitly requested.
- When running shell commands always use `poetry run` unless using `task`.
- Functions should be small and focused on a single task.
- Refactor long and complex code automatically.
- Add / update tests for any new functionality or significant changes.
- When writing tests, ensure they are isolated and do not depend on external state.
- Ensure that coverage is 100% after changes in affected code.