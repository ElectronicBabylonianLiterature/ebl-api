# TASK-740-qlty — TODO

Fix the 10 open `qlty:function-parameters` findings on PR #740.

qlty flags any function with **6 or more** parameters, so every target must
end at **5 or fewer**.

## Targets

- [x] Q1. `fragment_updater_test_helpers.py` — `expect_changelog` (6)
- [x] Q2. `test_fragment_updater.py` — `test_update_metadata_field` (8)
- [x] Q3. `test_fragment_updater_annotations.py` — `test_update_lemmatization` (6)
- [x] Q4. `test_fragment_updater_annotations.py` — `test_update_references` (7)
- [x] Q5. `test_fragment_updater_annotations.py` —
      `test_update_edition_metadata_field` (7)
- [x] Q6. `test_fragment_updater_annotations.py` —
      `test_update_lemma_annotation` (6)
- [x] Q7. `test_fragment_updater_annotations.py` —
      `test_update_named_entities` (7)
- [x] Q8. `test_introduction_route.py` — `test_update_introduction` (6)
- [x] Q9. `test_introduction_route.py` — `test_update_multiple_fields` (9)
- [x] Q10. `test_notes_route.py` — `test_update_notes` (6)

## Approach

- [x] A1. Do **not** simply shuffle the parameters into a new 6-parameter
      fixture — that moves the finding rather than fixing it. The gathering
      fixture must itself stay under the limit.
- [x] A2. Introduce a context object that owns the repeated mockito
      arrangement (`when`, `changelog`, `user`, repository, injector) and
      exposes intention-revealing helpers, so the change is a genuine
      readability win rather than linter appeasement.
- [x] A3. `expect_changelog` becomes a method on that context, which removes
      Q1 outright.
- [x] A4. Route tests (`test_introduction_route`, `test_notes_route`) need a
      separate, smaller context — different fixtures (`client`,
      `fragmentarium`, `database`).
- [x] A5. Assertions must stay semantically identical; no test may be
      weakened, skipped or removed.

## Gates

- [x] G1. `task format`
- [x] G2. `task lint`
- [x] G3. `task type` (pyre) — needs the temporary swap file
- [x] G4. `task type-pyright`
- [x] G5. `task test` — full suite, 0 failures
- [x] G6. 100% coverage on changed modules
- [x] G7. `poetry run flake8 <changed> --max-line-length=120`
- [x] G8. `poetry run mypy <changed> --ignore-missing-imports`
- [x] G9. `task lint-md`
- [x] G10. 250-line limit on every changed `*.py`
- [x] G11. Confirm no function in the touched files still has 6+ parameters
- [x] G12. Re-read the instructions; report gates; commit only if asked
