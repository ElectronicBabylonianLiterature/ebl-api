# TASK-740-qlty2 — TODO

Fix the 2 remaining `qlty:similar-code` findings on PR #740.

Both were introduced by the previous task (`TASK-740-qlty`): moving the route
tests onto `RouteContext` made the two edition-field tests structurally
identical, which tripped the duplication detector.

## Targets

- [x] D1. `test_introduction_route.py` — `test_update_introduction`,
      23 lines duplicated, mass 139
- [x] D2. `test_notes_route.py` — `test_update_notes`,
      21 lines duplicated, mass 139

## Approach

- [x] A1. The two tests differ only in the field name, the fixture supplying
      the values, and the `set_<field>` call. Extract one shared assertion
      helper parameterised by field name.
- [x] A2. Keep each test readable on its own — the test must still state
      which field it covers and where its data comes from.
- [x] A3. Check whether `test_update_invalid_introduction` and
      `test_update_invalid_notes` become the next duplicate pair once the
      first pair is collapsed; fix them in the same pass if so.
- [x] A4. Do not weaken any assertion. The same four checks must remain:
      POST status, POST body, GET body with `realiaInfo`, changelog entry.
- [x] A5. Do not reintroduce a function with 6+ parameters — the previous
      task's fix must stay intact.

## Gates

- [x] G1. `task format`
- [x] G2. `task lint`
- [x] G3. `task type` (pyre) — needs the temporary swap file
- [x] G4. `task type-pyright`
- [x] G5. `task test` — full suite, 0 failures, same test count
- [x] G6. 100% coverage on changed source modules
- [x] G7. `poetry run flake8 <changed> --max-line-length=120`
- [x] G8. `poetry run mypy <changed> --ignore-missing-imports`
- [x] G9. `task lint-md`
- [x] G10. 250-line limit on every changed `*.py`
- [x] G11. AST sweep: no function in the touched files has 6+ parameters
- [x] G12. Re-read the instructions; report gates; commit only if asked
