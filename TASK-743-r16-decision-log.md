<!-- markdownlint-disable MD013 -->

# TASK-743-r16-decision — Work Log

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Checked `git ls-files` for the name first, after overwriting two tracked task
  documents in the previous round by not doing so.
- Created this log and `TASK-743-r16-decision-todo.md` before starting.

### The decision

- **R14-4: the `copilot.instructions.md` change stays in PR #743.** Asked on
  2026-09-17; the answer was to leave it rather than split it into its own PR.
- No code or configuration changes follow from this. The change is already
  disclosed in #743's description, which asks for it to be reviewed as a rules
  change rather than slipping through inside a typing PR, so nothing further is
  needed to make it visible to a reviewer.
- R14-4 is therefore closed as *decided, keep*, not as *fixed*.

### Recorded in

- `TASK-743-r14-review.md` — R14-4's heading, its findings-table row, its detail
  section and the recommendation list all now carry the decision and its date.
- `TASK-743-r15-handoff.md` — R14-4 moved out of "open judgement calls"; the
  merge-checklist item is ticked.
- `TASK-764-r2-audit-todo.md` — step 8 closed.

### Final position

Every round-14 finding now has a status. R14-2 (the frontend `nameBreaks`
change) is the only one still open, and it cannot be closed from this
repository. Nothing was committed or pushed.
