# TASK-740-merge — TODO

Merge `origin/master` into `add-realia-annotation-api` and resolve all conflicts.

## Preconditions

- [x] Confirm working tree is clean before starting
- [x] Fetch `origin/master` and record ahead/behind counts (3 behind, 27 ahead)
- [x] Identify the incoming commits and the files they touch

## Merge

- [x] Run the merge (explicitly authorised by the user for this one merge)
- [x] Enumerate every conflicted path (2: `test_fragment_updater.py`,
      `test_fragment_updater_annotations.py`)
- [x] Resolve each conflict, preserving both master's intent and the branch's
      realia-annotation work
- [x] Fold master's new `test_fragment_updater_references.py` onto our
      `UpdaterContext` helper instead of leaving two parallel context dataclasses
- [x] Fix `test_references_route.py`, which auto-merged cleanly but was
      semantically broken (master's new test predates the `realia_info` param)
- [x] Re-check the data hard gate: `realia` and `namedEntities` remain separate
      arrays in the domain, the Mongo document and the wire; mixed input is a 422
- [x] Confirm no `*.py` file that this merge modified exceeds 250 lines

## Verification gates

- [x] `task format` — exit 0, 800 files already formatted
- [x] `task lint` — ruff, all checks passed
- [x] `task type` — pyre, no type errors (the gate CI enforces)
- [x] `task type-pyright` — 0 errors; plus an explicit pyright run on the
      touched modules, which the task's own file list would have missed
- [x] `task test` — 4068 passed, 2 skipped, 1 xfailed, 0 failures
- [x] `pytest --cov` — `fragment_updater.py` at 100%, 0 missing
- [x] `poetry run flake8 <touched modules> --max-line-length=120` — exit 0
- [ ] `poetry run mypy <touched modules> --ignore-missing-imports` — **one
      pre-existing error remains** (`lark_parser` module/package name
      collision). Raised to the user, not silenced: see the log.
- [x] `task lint-md` — 0 errors
- [x] Runtime verification: merged service run against local Mongo
      (`127.0.0.1:27017`, `.env` never sourced); 5 route checks all as expected

## Close-out

- [x] Leave the merge result uncommitted unless the user asks for a commit
- [x] Report what changed, which gates ran, and their results
- [ ] Remove `TASK-740-merge-*.md` before PR #740 is merged

## Open items for the user

1. **mypy** — `test_fragment_updater.py:20` reports `parse_atf_lark` missing
   because `atf_parsers/` holds both `lark_parser.py` and a `lark_parser/`
   grammar directory. Pre-existing, mypy-only; pyre, pyright and the runtime
   all disagree with it. A real fix is a repo-wide rename.
2. **250-line gate** — three files exceeding it arrive verbatim from master
   (`museum.py` 412, `lookup_reservations.py` 253,
   `test_bibliography_lookup_reservations.py` 282). Not caused by this merge.
