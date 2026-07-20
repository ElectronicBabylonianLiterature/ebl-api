# TASK afo-register-link — TODO

Repair `POST /afo-register/texts-numbers` so joined AfO references whose
`text` or `textNumber` contain spaces resolve to their records.

## Steps

- [x] Create branch from `master`
      (`fix-afo-register-texts-numbers-split`)
- [x] Reproduce against production (both curl cases from the prompt)
- [x] Read `mongo_afo_register_repository.py` and understand both query paths
- [x] Read existing tests (`test_afo_register_repository.py`,
      `test_afo_register_route.py`) and the record factory
- [x] Decide indexed `$or`-of-candidate-splits vs always-concat pipeline
      — chose the preferred `$or` (keeps the compound index; no measurement
      needed since the collection-scanning alternative was not taken)
- [x] Implement `candidate_splits`; build `$or` query across all queries
- [x] Drop `split_text_and_number` and `_build_indexed_query`
- [x] Drop `_build_fallback_pipeline` (unreachable once `$or` is equivalent)
- [x] Keep whitespace normalisation
- [x] Keep endpoint contract: array of strings in, records out
- [x] Add tests 1-6 from the prompt (repo level + route level)
- [x] Confirm existing tests pass unchanged
- [x] Check `.py` files stay under 250 lines (148 / 190 / 95)

## Gates before reporting complete

- [x] `task format` — 749 files already formatted
- [x] `task lint` — ruff, all checks passed
- [x] `task type` — pyre, no type errors (the gate CI enforces)
- [x] pyright — 0 errors (`task type-pyright` does not exist in this
      Taskfile; ran `npx pyright@latest` on changed files instead)
- [x] `task test` — 3848 passed, 2 skipped, 1 xfailed, 0 failures
- [x] coverage — 100% on the changed file (73 stmts, 0 missed)
- [x] `flake8 --max-line-length=120` — zero errors
- [x] `mypy --ignore-missing-imports` — zero errors
- [x] `task lint-md` — 0 errors
- [x] Run the modified backend service and exercise the affected route;
      re-verified after the rewrite against the shipping tree
- [x] Re-read copilot instructions; confirm every section honoured
- [x] Report uncommitted; do not commit

## Data hard gate check

- [x] `traditionalReferences` stays an array of joined reference strings —
      one data type per array. No mixed array introduced; contract unchanged.

## Left to the user

- Post-deploy check that <https://www.ebl.lmu.de/library/MNAO.11676> renders
  its AfO Register entries (requires a deploy).
- Remove this file and `TASK-afo-register-link-log.md` before the PR merges.
