# TASK-727 — Align Realia module with new data-prep schema

## TODO

- [x] Read current realia domain/schema/repository/seed/factory/tests
- [x] Verify new shape directly against `ebldev.realia` (lean ref, no content)
- [x] domain: remove `content` from `ReallexikonEntry`
- [x] schema: remove `content` field from `ReallexikonEntrySchema`
- [x] schema: deserialize lean `{id,pages}` reference -> Reference(DISCUSSION)
      (tolerate bare string; empty/missing id -> None)
- [x] Keep bibliography injection working (find AND search)
- [x] seed JSON / seed script: drop `content`, lean `{id,pages}` references
- [x] factory + tests: drop `content`, switch ref to `{id,pages}`
- [x] Add tests: (a) {id,pages} -> Reference w/ pages, (b) injection attaches
      document, (c) multi-entry injection
- [x] Pre-commit gates: format, full test, 100% cov on changed, flake8, mypy
- [x] Update log; remind to remove TASK-727-*.md before PR merge
