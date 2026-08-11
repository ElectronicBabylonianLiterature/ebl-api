# TASK-741-fix TODO

Address the findings raised in `TASK-741-review.md` for PR #741.

## Findings to address

- [x] **L1** — route limits admit up to 23,000 candidates while the repository
      caps at 10,000, so a route-validated request can still be rejected; the
      message also blames a single "query" when the cause is the batch
- [x] **L2** — `candidate_splits` annotated `object`, weakening type checking
      at every call site
- [x] **L3** — task-tracking files and the PR body's stale filenames
- [x] **I1** — candidate-count validation lives in the infrastructure layer
      while every other request-shape rule lives in the web layer
- [x] **I2** — whitespace normalization is query-side only

## Steps

- [x] Create task TODO and log (this file + `TASK-741-fix-log.md`)
- [x] Read the history behind the "restore candidate type guard" commit before
      touching the guard
- [x] Fix L1 + I1: validate the candidate budget at the route against the same
      constant, keep the repository bound as a backstop, reword both messages
- [x] Fix L2 without introducing a suppression or removing a test
- [x] Decide and record a rationale for I2 (no code change expected)
- [x] Update / add tests for every changed behaviour
- [x] Confirm no existing test needs removing; if one does, stop and ask first
- [x] 250-line limit on every touched `.py` file
- [x] 100% coverage on changed modules
- [x] `task format`, `task lint`, `task type` (pyre), `task type-pyright`,
      `mypy`, `flake8`
- [x] Full test suite
- [x] Re-run the modified service and re-exercise the route — the earlier run is
      void once the implementation changes
- [x] Update `TASK-741-review.md` to reflect the resolved findings
- [x] `task lint-md`
- [x] Ask before touching the PR body (outward-facing)
- [x] Re-read the copilot instructions; report which gates ran
- [x] Do **not** commit or push
