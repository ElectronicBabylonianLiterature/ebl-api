# TASK-named-entity-tags-review

Review of PR #731 — "Separate named-entity tags from part-of-speech in the
dictionary" (branch `separate-named-entity-tags` → `master`), **including the
merged-in PR #725 (`sum-lem`) changes**. Existing GitHub reviews and comments
on both PRs were fetched and incorporated (Sourcery, qlty, Codex, human
reviewer khoidt).

## Summary

The branch contains two change sets: (1) the `namedEntityTags` field +
migration, and (2) the merged PR #725 making `SUMERIAN`/`EMESAL` lemmatizable.
All gates pass and every outstanding GitHub finding is now addressed.

## Findings

### From GitHub — PR #731

- **G1 (Sourcery, fixed):** the migration called `logging.basicConfig` at
  import time, which can override logging config for any consumer that imports
  the module. Moved into `main()`.
- **G2 (qlty similar-code, fixed):** the 16-code list was flagged as duplicate
  structure. Collapsed `NAMED_ENTITY_CODES` to a single
  `frozenset("AN CN ... YN".split())`. Note: this set intentionally **differs**
  from `ebl/fragmentarium/domain/named_entity.py::NamedEntityType` (12 codes,
  includes `BN`, omits `AN/LN/QN/SN/TN`) — that is the fragmentarium annotation
  taxonomy, a separate concept; they must not be merged.
- **G3 (Sourcery, done):** task-tracking files. `TASK-…-todo.md` / `-log.md`
  were removed before merge; this review file remains and must be removed too.

### From GitHub — PR #725 (merged in)

- **G4 (Sourcery/Codex/khoidt F2, satisfied):** use enum members not
  `self.name` strings in `Language.lemmatizable`. The merge resolution already
  does this.
- **G5 (khoidt F3, satisfied):** simplify `GreekWord.alignable` to
  `self.lemmatizable` — present in the merge.
- **G6 (Codex P1 / khoidt F1, satisfied):** stale Sumerian "invalid alignment"
  test removed and positive `test_apply_sumerian_word` added — present in the
  merge.
- **G7 (Sourcery suggestion, done):** extracted module-level
  `LEMMATIZABLE_LANGUAGES` constant in `language.py` as the single source of
  truth for the `lemmatizable` property.

### From local diff review

- **A / B (verified correct):** `language.py` conflict resolution and
  `greek_tokens.py` `alignable` simplification are behaviour-correct and 100%
  covered.
- **C (informational, intended):** `SUMERIAN`/`EMESAL` are now lemmatizable
  everywhere `.lemmatizable` is consumed; a repo-wide grep found no other
  special-cases left inconsistent.
- **D (process, open — team decision):** PR #731 now carries PR #725's commits.
  Decide whether #725 is superseded by #731, merged independently first, or
  kept. No code action taken; not actionable unilaterally.

## Severity

- G1 — Medium — fixed (import-time side effect).
- G2 — Low — fixed (duplicate structure).
- G3 — Low — done (cleanup).
- G4–G6 — None — already satisfied by the merge.
- G7 — Low — done (clarity).
- A/B — None — verified correct.
- C — Informational — intended behaviour.
- D — Low — process / PR sequencing (open).

No high findings. Nothing blocks merge on correctness, regression, or security.

## Reproduction Steps

GitHub feedback fetched via:

- `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/{731,725}/reviews`
- `.../pulls/{731,725}/comments`
- `.../issues/{731,725}/comments`

Local verification after applying fixes:

- `poetry run pytest` (full suite) → green (run below).
- Coverage on touched modules → 100%:
  `migrate_named_entity_tags` (58/58), `language` (17/17), `greek_tokens`
  (48/48), and all dictionary modules.
- `poetry run ruff check ebl` / `ruff format --check` → clean.
- `poetry run pyre check` → no type errors.

## Recommendation

Approve. All GitHub and local findings are addressed except the process
decision in **D** (whether/how to retire PR #725), which is for the team.

> Reminder: remove this task tracking file
> (`TASK-named-entity-tags-review.md`) before the PR is merged.
