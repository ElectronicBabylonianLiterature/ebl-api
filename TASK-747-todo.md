# TASK-747 — Uppercase Ḫ/Ḥ collation (PR #747)

All work for PR #747 tracks here. One id per PR; earlier drafts wrongly used
invented ids `TASK-748` / `TASK-749`, which collide with real PR numbers.

## Phase 1 — Implementation (done)

Uppercase `Ḫ`, `Ḥ` and ASCII `H` must collate like their lowercase
counterparts, without depending on MongoDB's `$options: "i"`.

- [x] Reproduce the defect, patch `"collation H"`, re-run the probe
- [x] Tests: `ebl/tests/common/test_query_collation.py` and a realia
      repository search case
- [x] All gates green; runtime verified against a local MongoDB
- [x] Committed as `f9f58296`, pushed, PR #747 opened

## Phase 2 — Review (done)

- [x] Fetch reviews, inline comments and conversation comments
- [x] Confirm CI (19 checks pass) and qlty (no blocking issues)
- [x] Verify Sourcery's finding rather than taking it at face value
- [x] Export `TASK-747-review.md` with the required template

## Phase 3 — Address the findings (this phase)

| # | Finding | Action |
| --- | --- | --- |
| 1 | `\|` literal in char classes | Fix across all entries |
| 2 | Task files on the branch | Remove all `TASK-747-*.md` at the end |
| 3 | ASCII `H` broadens collated fields | None — intended, documented |
| 4 | Other groups keep the case gap | Deferred — flagged to the user |

- [x] Correct the task-file naming to `TASK-747-*`
- [x] Finding 1: removed the literal `|` from every collation class, character
      sets otherwise identical (applied by script, then verified)
- [x] Finding 1: `"collation SS"` kept faithful as `[sß]`, not `(ss\|ß)`
- [x] Finding 1: updated `COLLATED_H` in the test module
- [x] Finding 1: grepped for other assertions on an exact collation regex —
      only the test module referenced one
- [x] Finding 1: tests for a literal `\|` being escaped, a pipe query not
      matching a collated letter, an h-query not matching a stored pipe, and a
      parametrized guard that no entry contains a `\|`
- [x] Regression sweep — 4332 comparisons, zero behaviour changes
- [x] Gates: format, lint, pyre, pyright, test (4175 passed), coverage 100%,
      flake8, mypy, lint-md, all files under 250 lines
- [x] Runtime verification — H collation intact, pipe over-match gone
- [x] Updated `TASK-747-review.md` with the resolution of each finding
- [ ] Finding 2: delete `TASK-747-todo.md`, `TASK-747-log.md`,
      `TASK-747-review.md` — **pre-merge step, awaiting the user's word**
- [x] Report; commit only on an explicit request

## Phase 4 — Finding 4: close the case gap in the other groups (done)

- [x] Added the uppercase counterpart of every cased character in every
      collation class, mechanically via `str.upper()`
- [x] Skipped characters with no single-character uppercase (`ß` uppercases to
      `SS`) and caseless characters (`ᵈ`, `ₓ`, `ʾ`, digits, `+`)
- [x] Confirmed `"collation H"` unchanged — it already had its uppercase
- [x] Re-ran `ruff format` (`"collation O"` needed wrapping)
- [x] Verified the superset property: every class strictly gained characters,
      all of them uppercase counterparts, so no match can be lost
- [x] Tests: a parametrized invariant over all 29 collation entries, behaviour
      pairs across groups, and letters with no group staying literal
- [x] All gates green; `task test` 4242 passed
- [x] Runtime verification — `?query=Samas` now returns `Šamaš`
- [x] Updated `TASK-747-review.md`

## Known limitation (not a defect)

- Closing the case gap only helps letters that have a collation group.
  `b`, `f`, `j`, `m`, `p`, `q`, `v`, `w`, `z` have none, so an uppercase one
  stays literal: `Amel-Marduk` does not match `amêl-marduk` at the regex
  level because of the `M`. Those cases keep relying on the `$options: "i"`
  that every collated query already sets.

## Remaining

- Finding 2: delete `TASK-747-todo.md`, `TASK-747-log.md` and
  `TASK-747-review.md` before the PR is merged.
