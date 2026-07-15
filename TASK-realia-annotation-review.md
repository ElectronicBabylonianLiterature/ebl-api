# TASK-realia-annotation — Review

## Summary

Reviews branch `add-realia-annotation-api` (6 commits ahead of `master`,
`aa507ed4..0a66f569`; ~2,400 insertions across 56 files). The change adds a
second, structurally separate annotation kind (**realia**) alongside named-entity
tags on fragments, wires a realia existence check and referential integrity into
the annotation POST, and embeds resolved realia display info into the fragment
GET response. Supporting refactors split two over-length modules
(`domain/fragment.py`, `transliteration/domain/text.py`).

**Data hard-gate verdict: PASS.** The two annotation kinds are separated
structurally at every level — wire (`namedEntities` vs `realia`), `Fragment`
(`named_entities` vs `realia`), and `Word` (`named_entities` vs `realia`). No
array mixes types, no discriminator/`OneOfSchema` probing survives, and the
shared id namespace invariant (id uniqueness) is enforced across the **union** of
both arrays in `NamedEntityResource._validate_unique_ids`. Mixing is rejected for
free by `unknown=RAISE` (a `realiaId` inside `namedEntities` is an unknown-field
`422`, and vice versa).

**Existing PR feedback:** No open GitHub PR exists for this branch (only the
remote branch `origin/add-realia-annotation-api` is present; `gh pr list` and the
pulls API return nothing). There is therefore no submitted review, inline, or bot
feedback to incorporate. Re-run the review-guidelines feedback fetch once a PR is
opened.

**Local verification:** targeted + blast-radius suites run green — 249 realia/
annotation/metadata/route tests plus 194 token/dtos/fragment tests, no
regressions. The full suite was not run to completion here (it exceeds the
sandbox time limit); the work log records `3874+ passed`.

## Findings and resolutions

All findings below have been addressed (see `TASK-realia-review-fixes-log.md`).
Two were self-corrected on a closer read of the tests: **F4 was withdrawn** and
**F5 was reclassified as intentional**.

### F1 — Relocated markup-error branch was uncovered (coverage hard-gate) — FIXED

`ebl/fragmentarium/domain/fragment_metadata.py:19-20` — the
`except PARSE_ERRORS: raise ValidationError("Invalid markup: …")` branch of
`parse_markup_with_paragraphs` was not exercised by any test. The whole file is
newly created by relocating code out of `fragment.py`, so under the copilot
coverage hard gate ("Any line you add, modify, move, **or relocate** must end at
100%") this branch had to be covered.

**Resolution:** added `test_parse_markup_with_paragraphs_rejects_invalid_markup`
(and an empty-input companion) to `test_fragment_metadata.py`.
`fragment_metadata.py` now reports 100%. **Severity: Medium.**

### F2 — Realia existence check was N queries + needless bibliography joins — FIXED

`ebl/fragmentarium/web/named_entities.py` — `_validate_realia_ids` called
`find_by_realia_id` once per distinct id, each going through
`_load_entry → _inject_bibliography` (two DB round-trips per id, including a
bibliography fetch that an existence check does not need).

**Resolution:** rewritten to a single batch `find_by_realia_ids(sorted(...))`
call, compare the returned realia-id set against the requested set, and raise
`DataError` listing any missing ids. The error still names the unknown id, so
`test_reject_unknown_realia_id` passes unchanged. **Severity: Low.**

### F3 — Fragment GET issued an empty `$in` query with no realia — FIXED

`ebl/fragmentarium/application/realia_info.py` — `resolve_realia_info` ran on
every single-fragment GET and issued `find_many({"realiaId": {"$in": []}})` even
when the fragment had no realia.

**Resolution:** short-circuit `if not realia_ids: return []`. Updated
`test_resolve_empty_without_realia` to assert the repository is no longer called
(`repository.calls == []`). **Severity: Low.**

### F4 — WITHDRAWN (not a defect)

Original finding claimed the annotation POST should populate `realiaInfo` for
parity with GET. This is **intentional by design**:
`test_realia_info_route.py::test_write_neither_requires_nor_stores_realia_info`
asserts the write response omits `realiaInfo` and that a client-supplied
`realiaInfo` in the payload is ignored. `realiaInfo` is a GET-only, read-side
projection; writes stay lean and the client re-fetches. My exploratory change was
reverted. **No action; review corrected.**

### F5 — `RealiaInfoSchema` load path — INTENTIONAL, no change

The load path is not dead: `test_realia_info.py::test_schema_load` deliberately
exercises `.load` and the `post_load`, keeping the schema round-trippable.
Removing tested code would also require explicit approval per the copilot
test-removal gate. **Reclassified as an intentional design choice; no action.**

### F6 — Process hygiene — ACKNOWLEDGED

The branch commits `TASK-*.md` scaffolding and process/tooling edits
(`.github/instructions/copilot.instructions.md`, `.claude/settings.json`)
alongside the feature. Per the copilot task-tracking rule, all `TASK-*.md` files
(this review and the fix logs included) must be removed before merge. Consider
splitting the governance/tooling changes from the feature for a cleaner history.
**Severity: Low / observation.**

## Severity

| ID | Severity | Area | Status |
| --- | --- | --- | --- |
| F1 | Medium | Test coverage (hard gate) | Fixed |
| F2 | Low | Efficiency / DB access | Fixed |
| F3 | Low | Efficiency / DB access | Fixed |
| F4 | — | (misread) | Withdrawn |
| F5 | — | (intentional) | No action |
| F6 | Low | Process / hygiene | Acknowledged |

No correctness, data-shape, security, or regression defects were found. The data
hard-gate separation is correct and complete.

## Reproduction Steps

- **F1** — `pytest ebl/tests/fragmentarium/test_fragment_metadata.py
  --cov=ebl.fragmentarium.domain.fragment_metadata --cov-report=term-missing`;
  before the fix, lines `19-20` were reported missing.
- **F2** — Read `named_entities.py::_validate_realia_ids`; before the fix,
  `find_by_realia_id` (`mongo_realia_repository.py:44` → `_load_entry` →
  `_inject_bibliography:110`) ran once per id ⇒ 2·k queries for k ids.
- **F3** — Read `realia_info.py::resolve_realia_info`; before the fix,
  `find_by_realia_ids([])` reached `find_many({"realiaId": {"$in": []}})` on any
  no-realia GET.
- **F4** — `test_write_neither_requires_nor_stores_realia_info` documents the
  intended write-side omission.
- **F5** — `test_realia_info.py::test_schema_load` exercises the load path.

## Recommendation

**Approve.** The core design is sound and fully satisfies the data hard gate.
All actionable findings (F1–F3) are fixed in the working tree; F4/F5 were
self-corrected as non-issues. Verified locally:

- `fragment_metadata.py`, `web/named_entities.py`, `application/realia_info.py`
  at 100% coverage on changed lines.
- 443 targeted/blast-radius tests pass, no regressions.
- `ruff format` clean, `ruff check` clean, `flake8 --max-line-length=120` clean,
  every changed file under the 250-line gate, and `mypy --ignore-missing-imports`
  introduces zero new errors in the changed source files.

Before merge: remove all `TASK-*.md` (F6), including this review file. Changes are
uncommitted; no commit was authorized.

_Delete this file (`TASK-realia-annotation-review.md`) before the PR is merged._
