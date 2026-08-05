# TASK-747 — Add Ḫ and Ḥ to the query collation

## Goal

Uppercase `Ḫ`, `Ḥ` (and ASCII `H`) must collate in search queries the same way
their lowercase counterparts already do, so that `Ḫattusa` / `Ḥattusa` /
`Hattusa` all reach `h`, `ḫ` and `ḥ` in the stored data without depending on
MongoDB's `$options: "i"` case folding.

## TODO

- [x] Read `.github/instructions/copilot.instructions.md` and honour every gate
- [x] Create `TASK-747-todo.md` and `TASK-747-log.md` before starting work
- [x] Confirm clean tree on `master`, create branch `add-uppercase-h-collation`
- [x] Reproduce the defect against the current file (probe script, no MongoDB)
- [x] Apply the recommended patch to `"collation H"` in
      `ebl/common/query/query_collation.py`
- [x] Re-run the probe and confirm all four spellings collate
- [x] Add repository-level test in
      `ebl/tests/realia/test_realia_repository_search.py`
      (store `Ḫattusa`, search `Hattusa` and `ḥattusa`)
- [x] Add unit tests for the collation itself (uppercase segments collate;
      non-collation characters still rejected)
- [x] Check `ebl/tests/dictionary/test_word_repository.py` for assertions on
      exact regex strings for `h`-initial lemmas — none exist
- [x] Confirm no `.py` file exceeds 250 lines (209 / 62 / 159)
- [x] Gate: `task format` — 801 files already formatted
- [x] Gate: `task lint` — all checks passed
- [x] Gate: `task type` (pyre — the CI gate) — no type errors
- [x] Gate: `task type-pyright` — reported no changed files (nothing committed),
      so pyright was run directly on the changed files: 0 errors
- [x] Gate: `pytest --cov=ebl.common.query.query_collation
      --cov-report=term-missing` — 100%
- [x] Gate: `flake8 <changed modules> --max-line-length=120` — 0 errors
- [x] Gate: `mypy <changed modules> --ignore-missing-imports` — no issues
- [x] Gate: `task lint-md` — 0 errors
- [x] Gate: `task test` — 4110 passed, 2 skipped, 1 xfailed
- [x] Runtime verification: patched service run against local MongoDB
      (`127.0.0.1:27017`), `GET /realia?query=…` returns `Ḫattusa` for every
      H-spelling and still rejects `Xattusa`
- [x] Re-verify after any rewrite of the implementation — no rewrite followed
      the runtime run
- [ ] Report to the user; commit/push/PR only on explicit request
- [ ] Remind to remove `TASK-747-*.md` before the PR is merged

## Out of scope

- The systemic alternative (`re.IGNORECASE` on `_is_regex` and `_segmentize`),
  which would fix every collation group at once but leaves the emitted class
  lowercase and so relies on `$options: "i"`. Recorded in the log as the
  rejected option.
- The other collation groups (`Š`, `Ṣ`, `Ṭ`, `Ā`, …) have the same gap; the
  request was for `Ḫ` and `Ḥ`.
