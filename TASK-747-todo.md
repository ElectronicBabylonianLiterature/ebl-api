<!-- markdownlint-disable MD013 -->
# TASK-747 — TODO: move the DB-related changes out of PR #743

User asked for all DB-related changes to leave #743 and go to a new PR,
after the finding that migrating before the new backend deploys breaks
production (`ValidationError: nameBreaks: Unknown field`).

## 1. Decide exactly what is "DB-related"

- [x] `task_743_migrate_name_breaks.py` — moves
- [x] `task_743_migrate_name_breaks_test.py` — moves
- [x] `@pre_load` adapter `separate_legacy_name_parts` — **STAYS.** Verified:
      without it the new code cannot read any existing document
      (`Must be equal to ValueToken`). It is deploy compatibility, not a data
      change
- [x] Checked the rest of the diff: the `mongo_*` files are type/import
      changes only; the aggregation key rename is an internal projection

## 2. Prepare the split

- [x] Branch `migrate-name-breaks` off `origin/master`, worktree at
      `/workspaces/ebl-migrate-name-breaks`
- [x] Migration files onto it; 18 passed, 100% coverage there
- [x] Removed from `fix-type-checker-blind-spots`; no dangling references

## 3. Gates on the reduced #743 branch

- [x] format, lint, pyre, pyright, coverage, flake8, mypy, qlty, lint-md — all
      pass with the migration files gone; `task test` 4530 passed

## 4. Documentation

- [x] Gate 2 rewritten: moved out of #743, post-deploy, its own PR
- [x] Gate 3 updated — still sixteen files, now all documentation
- [x] Rolling-deploy window and the `unknown = RAISE` trap recorded

## 5. Close-out

- [x] Re-read the instructions file; gates and results stated
- [ ] STOP before every `git commit`, `git push` and `gh pr create` and ask —
      asking for a PR is NOT commit approval

## 6. Awaiting the user

- [ ] Commit the removal on `fix-type-checker-blind-spots` — needs explicit ask
- [ ] Commit the two files on `migrate-name-breaks` — needs explicit ask
- [ ] Push and open the migration PR — needs explicit ask, and should wait until
      #743 is deployed
- [ ] Decide: does the migration PR merge, or is it closed after the run?
- [ ] Decide: rename the files to drop the `task_743_` prefix?
