# TASK-727 Work Log — Align Realia module with new data-prep schema

## 2026-06-24

- Read current realia domain/schema/repository/seed/factory/tests.
- Verified the new shape directly against `ebldev.realia` (24,197 docs):
  - `reallexikon[].content` removed everywhere (0 docs have it).
  - Every `reallexikon[].reference` is a lean `{id, pages}` object
    (sampled 3,288 entries, all `{id, pages}`); 0 with empty id / missing
    pages / null. Document-level `references[]` unchanged.
- Changes:
  - domain `ReallexikonEntry`: removed `content`.
  - schema `ReallexikonEntrySchema`: removed `content` field.
  - `ReallexikonReferenceField._deserialize`: now builds a `Reference`
    directly from a lean `{id, pages}` dict (DISCUSSION type, pages preserved);
    still tolerates a bare string; empty/missing id and unexpected types -> None
    (ApiReferenceSchema can't load the lean object since it requires
    type/notes/linesCited).
  - Kept bibliography injection (`_inject_bibliography` / `_inject_reallexikon`
    / `_collect_reference_ids`) — resolves `reference.id` against the
    `bibliography` collection and attaches `document` on find AND search.
  - seed `realia-seed-pig.json`: dropped `content`; references now lean
    `{id, pages}` (two entries) plus one `null` to exercise both paths.
    `scripts/seed_realia.py` needed no change (generic loader).
  - factory: dropped `content`.
  - tests: dropped `content`, switched stored-shape refs to `{id, pages}`.
    Added: (a) lean `{id,pages}` -> Reference(DISCUSSION) with pages preserved,
    empty/unexpected -> None; (b) injection attaches bibliography `document`
    to a reallexikon reference (pages preserved); (c) multi-entry doc injects
    all entries, null reference stays null.
- Verified end-to-end on live `Aššur`: served reallexikon reference is
  `{id, type, pages, notes, linesCited, document}`, document injected, no
  `content`.
- Gates: `task format` clean; realia tests 38 passed; 100% coverage on both
  changed source modules; flake8 0; mypy 0. Full `task test` run pending.

(Reminder: remove TASK-727-todo.md / TASK-727-log.md before this PR is merged.)
