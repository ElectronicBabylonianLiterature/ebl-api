# TASK-764-r4-docs — Work Log

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Checked `git ls-files` for both names before creating them.
- Created this log and `TASK-764-r4-docs-todo.md` before starting.

### The request, and the concern I had already raised

- I had deliberately left every `TASK-*.md` untracked, because committing one
  reopens the stray-files finding that both branches were just cleaned for.
  I said so in the handoff and in my report.
- The user asked for the documents to go into the commit anyway. That is their
  call; it is recorded here and reflected in the handoff rather than argued
  again. The consequence is that the merge-time cleanup now has to remove them
  from #764 as well.
- `d83582a2` has not been pushed — the remote is at `31929977` — so amending it
  rewrites nothing that anyone else has seen.

### Work

- Corrected `TASK-CURRENT-handoff.md` first. It opened with "Do not commit this
  file, or any `TASK-*.md`" — committing it unchanged would have shipped a
  statement contradicted by the commit containing it. It now records that the
  documents are tracked on this branch by choice and must be removed before #764
  merges, and the merge checklist says the same.
- Staged every task document on disk and amended `d83582a2`.
- No `*.py` file changed, so the Python gates confirmed for `d83582a2` still
  stand: format, ruff, pyre, pyright, mypy, flake8 and qlty clean, 4556 passed,
  `migrate_name_breaks.py` at 100% coverage. `task lint-md` re-run for the
  markdown: 0 errors across 21 files.

### Consequence, recorded rather than argued

`git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'`
now returns the task documents on `migrate-name-breaks` instead of nothing. The
gate that check enforces is unchanged — nothing may reach `master` — so the
cleanup simply moves to merge time, and the handoff carries the command.

<!-- markdownlint-configure-file { "MD013": false } -->
