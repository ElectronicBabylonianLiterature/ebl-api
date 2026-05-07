# TASK-711 — TODO

## Findings to address

- [x] **F1** — Replace two-pass parser with iterative peel loop handling arbitrary nested/mixed wrappers and trailing markers.
- [x] **F2** — Preserve legacy raw value via new `original_value` / `originalValue` field so DB reads are not lossy.
- [x] **F3a** — Shallow-copy `data` in parser to avoid mutating Marshmallow's dict.
- [x] **F3b** — Add docstring describing rule precedence and intentional leniency.
- [x] **F4** — Skip strip when a flag is caller-set (non-`None`); parser-set flags do not block re-peeling so `<<5>>` collapses.
- [x] **F5** — Default `value` to `""` only when missing; documented in docstring.
- [x] **F6** — Documented intentional leniency in docstring.
- [x] **F7** — Added behavioral tests:
  - [x] Mixed-marker patterns (`<n>?`, `<n>!`, `[n]?`, `[n]!`, `(n)!`).
  - [x] Nested/multi-layer (`[(5!)]?`, `([5?])!`, `[<(5)>]`, `<<5>>`).
  - [x] Degenerate inputs (`<>`, `[]`, `()`, `!`, `?`, `""`).
  - [x] `original_value` round-trip via `DateSchema` (legacy DB shape).
  - [x] `MonthSchema` / `DaySchema` silently EXCLUDE `isReconstructed` / `isEmended`.
  - [x] Updated existing F4-related test (added True/False variants).
  - [x] Input-mutation regression test.
- [x] **F8** — Maintained task docs; `TASK-711-{todo,log,review}.md` to be deleted before merge.
- [x] Run full date-related test suite — **43 passed**, 100% coverage on `date.py`.
- [x] Wider regression check — **726 passed** in `ebl/tests/fragmentarium/`.

## Pre-merge

- [ ] Remove `TASK-711-todo.md`, `TASK-711-log.md`, `TASK-711-review.md` immediately before PR merge.
