# TASK-764-commit LOG — Commit the outstanding task documentation

## Entries

### 1. Task start

- Request: commit all the changes. That authorises exactly one commit, of the
  changes under discussion, and does not extend to a push.
- The uncommitted changes are `TASK-764-checks-todo.md` and
  `TASK-764-checks-log.md` from the previous task, plus this task's own pair.
  No Python has changed since `24ff519b`.
- `TASK-764-schema-todo.md` and `TASK-764-schema-log.md`, created during the
  schema lookup, were deleted from disk by someone other than me between that
  task and this one. They were never tracked, so git records nothing about
  them. They have not been recreated: removing task files at the user's request
  settles that task, and recreating them uninvited would undo a deliberate
  cleanup.
- `24ff519b` is on the remote, so this must be a new commit. Amending it would
  rewrite pushed history, which is forbidden without a specific request.

### 2. Ordering, learned from the earlier mistake

The first amend in this session left the log and TODO dirty because the
close-out was written after committing. This time the closing entries are
written first, phrased so they stay accurate once the commit exists, and the
commit refers to itself by description rather than by hash.

### 3. Pre-commit hard gates

Run in order before committing; results recorded in the report. The change is
markdown only — no Python differs from `24ff519b` — but the gate list is not
conditional on what changed, so all eight were run, plus `task lint-md`.

### 4. Commit

- Staged everything, including this file and its TODO, so the working tree is
  clean afterwards with nothing left over.
- Not pushed: a push was not requested in this message.

### 5. Note on the interrupted request

The message before this one, "I need the schema here", was interrupted before I
acted on it. Nothing was done about it. It is not part of this commit and needs
clarifying: it could mean cherry-picking #743's `NamedSignSchema` change onto
this branch, or something narrower.
