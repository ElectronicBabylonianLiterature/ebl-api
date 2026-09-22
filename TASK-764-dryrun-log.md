# TASK-764-dryrun — Work Log

Records what was actually done, including every error and how it was recovered.

## Entries

### Start

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Created this log and `TASK-764-dryrun-todo.md` before starting the work.
- Branch is now `migrate-name-breaks` (PR #764) at `31929977`, not
  `fix-type-checker-blind-spots`. The round-14/15 task documents from the
  previous task are present as untracked files carried across the switch.

### Safety verification before connecting to anything

- Read `ebl/transliteration/migrate_name_breaks.py` (207 lines) end to end.
- **Proved the dry-run path is read-only.** The only two write calls,
  `collection.bulk_write` at lines 144 and 147, both sit inside `_apply_updates`,
  which is reached only from `migrate_collection` when `dry_run` is false, and
  `main` sets `dry_run=not arguments.apply`. Without `--apply` the reachable
  Mongo surface is `find({})` and `list_collection_names()` and nothing else.
  Confirmed by an AST walk for every pymongo write method, not by reading alone.
- `poetry run pytest` on the migration's own two test files: 27 passed.
- **Local rehearsal** against a scratch database at `127.0.0.1:27017`: seeded
  legacy, already-migrated and no-sign documents. Dry run reported the right
  counts, and a before/after comparison of every document proved the database
  was left byte-identical, with no `nameBreaks` written.
- **Rehearsed the failure path** too: with three malformed documents present the
  dry run aborts on the **first** one and names it, reporting nothing about the
  other two. Worth knowing — the script alone cannot enumerate all offenders.

### Target

- `.env` in this container sets `MONGODB_DB=ebldev`, while the connection
  string's own default database is `ebl`. Raised the discrepancy rather than
  guessing; the answer was **`ebldev`**, which matches the database the app
  itself opens via `os.environ.get("MONGODB_DB")` in `create_context`.
- Read preference: **`secondaryPreferred`**, appended to the URI so the full
  scan does not load the primary. The script was not modified to achieve this.

### Dry run — result

`poetry run python -m ebl.transliteration.migrate_name_breaks` (no `--apply`),
`MONGODB_DB=ebldev`, `readPreference=secondaryPreferred`. Exit 0, **no
`NonAlternatingName` abort**:

| Collection | Documents that would be migrated |
| --- | --- |
| `fragments` | 38 284 |
| `texts` | 0 |
| `chapters` | 220 |

### Census — full enumeration, because the script stops at the first offender

A separate read-only pass over the same database, checking **every** name array
through the script's own `separate_name_parts` rather than stopping at the first
failure:

| | `fragments` | `texts` | `chapters` |
| --- | --- | --- | --- |
| documents | 328 422 | 84 | 298 |
| documents holding names | 38 284 | 0 | 220 |
| needing migration | 38 284 | 0 | 220 |
| already migrated | 0 | 0 | 0 |
| name arrays | 4 970 779 | 0 | 538 090 |
| breaks inside names | 211 973 | 0 | 38 245 |
| **non-alternating names** | **0** | **0** | **0** |

**5 508 869 name arrays checked, 250 218 breaks, zero violations.** The
`texts: 0` from the dry run is confirmed as "this collection holds no named
signs", not a false negative — all 84 documents were read and none contains a
`nameParts` array. Nothing is already migrated, as expected while the backend
that writes the new shape is still unmerged.

### Outcome

PR #743's Gate 2 is satisfied for `ebldev`: a clean dry run exists, and the
stronger census shows no document anywhere in the database would be mis-split
by the positional adapter. Nothing was written. `--apply` was not run.

<!-- markdownlint-configure-file { "MD013": false } -->
