# TASK-740 TODO — Fix pyre error and gate against it

Task: CI failed with a pyre type error that the pre-commit gates missed.
Fix it, and add a blocking gate so it cannot recur.

## Diagnose

- [x] Reproduce with `task type`:

```text
ebl/fragmentarium/web/fragments.py:92:46 Unexpected keyword [28]:
Unexpected keyword argument `strict` to call `zip.__new__`.
```

- [x] Root cause: `strict=True` (Python 3.10) is rejected by pyre's bundled
      typeshed; ruff `B905` demands it. The two checkers contradict.
- [x] Why it was missed: `task type` (pyre) is not in the pre-commit gate
      list; mypy and pyright both passed and I inferred pyre had too.

## Fix

- [x] Remove the `zip` entirely rather than satisfy one checker over another
- [x] `resolve_realia_info_map` returns `{realia_id: RealiaInfo}`
- [x] `document_realia_info(document, map)` per-document lookup
- [x] Update `fragments.py` to key lookups instead of positional pairing
- [x] Confirm one batched query is preserved
- [x] `fragments.py` back under 250 lines (249)

## Gates (all four checkers this time)

- [x] `task type` (pyre) — No type errors found
- [x] `task type-pyright` / pyright on changed files — 0 errors
- [x] `poetry run mypy <changed>` — 0 errors in changed files
- [x] `task lint` (ruff) — B905 no longer applies; all checks passed
- [x] `task format` — clean
- [x] `task test` — 3923 passed
- [x] Coverage on changed modules — 100%
- [x] `task lint-md` — 0 errors
- [x] `task test-all` (aggregate) — exit 0
- [x] Run the modified backend service and verify the rewritten resolution

## Prevent recurrence

- [x] Add `task type` + `task type-pyright` to the pre-commit gate list
- [x] Add "All Three Type Checkers Must Pass" hard gate
- [x] Record the `zip`/`strict` contradiction as a worked example
- [x] Verify `task test-all` is the real task name (`task check` does not
      exist — caught by running it)
- [x] Elevate task tracking to a hard gate: docs created BEFORE work starts
- [x] Persist the recurring failure to memory so it survives the session

## Reminders

- `TASK-740-todo.md` and `TASK-740-log.md` must be removed before merge.
- Nothing is to be committed unless explicitly requested.
- CI is red until the fix is committed; the fix is uncommitted.
