# TASK-743-fixes — TODO

Fix the four issues identified during the `master` → `fix-type-checker-blind-spots`
merge (see `TASK-743-merge-log.md`). **No commits** — the user reviews first.

## Constraints

- All three type checkers must stay green: `task type` (pyre, CI-enforced),
  `task type-pyright`, and `mypy`. Fixing one must not break another.
- No suppressions: no `# type: ignore`, no `# noqa`, no lint/formatter config
  edits. Fix the real problem.
- No `*.py` file may exceed 250 lines.
- Never remove or weaken an existing test.
- 100% coverage on every line added, modified, moved, or relocated.

## 1. `docs/ebl-atf.md` typo

- [x] Checked the stashed edit (`stash@{0}`) — it contained **only** the
      corruption, so nothing was restored
- [x] No repair needed: the merged file already reads `defined in
      [ebl-atf.lark]`, and the corruption is absent from the working tree
- [x] `task lint-md` clean
- [ ] User decision outstanding: drop `stash@{0}`, or keep it?

## 2. flake8 E501 in `ebl/fragmentarium/domain/museum.py`

- [x] Line 130: 167-char URL exceeds the 120 limit
- [x] Fix without `# noqa` and without changing the URL value
- [x] `flake8 --max-line-length=120` clean on the file

## 3. 42 mypy errors across 31 files

- [x] Enumerate the full error list and group by root cause
- [x] Fixed 40 of 42; 2 remaining are environmental (see log)
- [ ] `mypy --ignore-missing-imports` down to **2** errors, not 0. Both are
      `Library stubs not installed for "requests"`, caused by `mypy` being a
      global pipx install that cannot see the project venv — an environmental
      issue, not a code defect. Needs a user decision (see log).

## 4. Three files over the 250-line hard gate

- [x] `ebl/fragmentarium/domain/museum.py` (412)
- [x] `ebl/tests/bibliography/test_bibliography_lookup_reservations.py` (282)
- [x] `ebl/bibliography/infrastructure/lookup_reservations.py` (253)
- [x] Split by extracting modules / splitting test files, preserving behaviour
      and every existing test

## Final gates (all must pass before reporting done)

- [x] `task format`
- [x] `task lint`
- [x] `task type` (pyre)
- [x] `task type-pyright`
- [x] `task test`
- [x] coverage: 100% on every line added, modified or moved (two of my own
      lines were uncovered and are now covered by new tests). Pre-existing
      gaps in files I touched are listed in the log and left as they were.
- [x] `flake8 --max-line-length=120` on changed modules
- [x] `mypy --ignore-missing-imports` on changed modules
- [x] `task lint-md`
- [x] Runtime verification of the running service
- [x] Report; **nothing committed** — working tree only
- [x] Remind to remove TASK docs before the PR is merged
