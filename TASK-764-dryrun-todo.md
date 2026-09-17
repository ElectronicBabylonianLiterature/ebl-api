<!-- markdownlint-disable MD013 -->

# TASK-764-dryrun — TODO

Run the `nameParts` / `nameBreaks` migration in dry-run mode, on branch
`migrate-name-breaks` (PR #764). This closes Gate 2 of PR #743.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] TODO + log created before any work (this file + `TASK-764-dryrun-log.md`)
- [x] Nothing committed or pushed, push, merge, rebase or reset without an explicit request
- [x] No test removed, disabled or skipped without explicit approval
- [x] No linter / formatter / type-checker configuration modified
- [x] Use `poetry run` or `task` for every project command

## Safety gates specific to this task

- [x] Read the migration script in full **before** running anything
- [x] Proved the dry-run path performs **no writes** — no `update`, `insert`,
      `replace`, `delete` or `bulk_write` reachable without `--apply`
- [x] Confirmed the target database before connecting; `.env` `MONGODB_URI` is the
      live production cluster
- [x] `--apply` not run. Dry run only.

## Steps

- [x] 1. Locate the migration script and its tests on this branch
- [x] 2. Read the script end to end; record what dry-run does and does not do
- [x] 3. Verify read-only by inspection, then by a rehearsal against a local
      scratch database seeded with legacy-shape documents
- [x] 4. Confirm the production target with the user before connecting
- [x] 5. Run the dry run against production
- [x] 6. Record the counts, and any `NonAlternatingName` findings, in the log
- [x] 7. Report the result, and what it means for PR #743's Gate 2
