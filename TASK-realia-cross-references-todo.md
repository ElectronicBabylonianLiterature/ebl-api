# TASK-realia-cross-references — TODO

## Feature

- [x] Add domain types `CrossReference` (`{id, lemma}`) and
  `AfoCrossReference` (`{id, lemma, afoVolume, page}`).
- [x] Add `realia_id`, `cross_references`, `afo_cross_references` to
  `RealiaEntry`; add `afo_volume`, `page`, `cross_references` to
  `AfoRegisterEntry` (lists default to `()`).
- [x] Add marshmallow schemas with validation: cross-references require
  `id`+`lemma`; AfO cross-references additionally require `afoVolume`+`page`;
  lists default to `[]`.
- [x] Wire new fields into `AfoRegisterEntrySchema` and `RealiaEntrySchema`.
- [x] Add `find_by_realia_id` to the repository (abstract + Mongo) keyed on
  the stable `realiaId` field.
- [x] Add `RealiaByIdResource` and route `GET /realia/by-id/{realia_id}`,
  keeping the lemma-keyed route.

## Audit / gates (Copilot instructions)

- [x] Keep every `*.py` under 250 lines — extracted `realia_schemas.py`,
  split test files, shared helpers in `realia_repository_helpers.py`.
- [x] Update factories for the new fields.
- [x] 100% coverage on all changed source modules.
- [x] `black`, `ruff`, `flake8 --max-line-length=120` clean.
- [x] `mypy` (changed files) and `pyre` clean.
- [x] Full test suite green (3752 passed).
- [x] Author review file `TASK-realia-cross-references-review.md`.

## Before merge

- [ ] Remove `TASK-realia-cross-references-*.md` tracking files.
- [ ] Confirm whether the dev-only seed script/data should be removed.
