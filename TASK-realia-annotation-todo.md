# TASK-realia-annotation — TODO

Add realia annotation support to the named-entities API.

## Domain

- [x] `RealiaEntity(id, realia_id)` in `ebl/fragmentarium/domain/named_entity.py`
- [x] `RealiaAnnotationSpan(RealiaEntity)` with `span` and `to_named_entity()`
- [x] Union aliases `AnnotationEntity` / `AnnotationSpan`
- [x] Replace `NamedEntity` / `EntityAnnotationSpan` references with the aliases

## Schema

- [x] `RealiaEntitySchema` / `RealiaAnnotationSpanSchema` with `data_key="realiaId"`
- [x] `realiaId` validated against `^realia_\d+$`
- [x] Polymorphic dispatch on presence of `realiaId` (load) / entity class (dump)
- [x] Both `type` and `realiaId` -> `ValidationError`
- [x] Neither `type` nor `realiaId` -> `ValidationError`
- [x] Unknown key still raises (`unknown=RAISE` preserved)
- [x] Decide on `RealiaRepository.find_by_realia_id` existence check

## Fragment / text

- [x] `Fragment.named_entities: Sequence[AnnotationEntity]`
- [x] `Fragment.set_named_entities(annotations: List[AnnotationSpan])`
- [x] `Text.set_named_entities(annotations: List[AnnotationSpan])`
- [x] Realia ids written into the same `word.named_entities` list

## Web

- [x] `_create_annotation_spans` echoes `realiaId` on GET
- [x] `on_post` keeps `transliterate:fragments` scope
- [x] Stable ordering of returned spans
- [x] `ValidationError` -> `DataError` (422)

## Persistence

- [x] `FragmentSchema.named_entities` nests the polymorphic entity schema
- [x] `mongo_fragment_repository.update_field("named_entities", ...)` unchanged
- [x] Legacy entity-only documents load unchanged

## Tests

- [x] Round-trip entity span + realia span
- [x] Round-trip realia span and entity span over the same token range
- [x] Reject `realiaId` + `type` on one object
- [x] Reject neither `type` nor `realiaId`
- [x] Reject malformed `realiaId` (`Apkallu`, `realia_`, `realia_abc`)
- [x] Reject unknown extra key
- [x] Legacy entity-only GET returns pre-existing shape byte-for-byte
- [x] Deleting a realia span removes its id from every `word.named_entities`
- [x] Unknown `realiaId` rejection (if existence checking implemented)

## Types / Pylance

- [x] `pyright <touched files>` — zero errors (all 18 fixed, none suppressed)
- [x] Pre-existing Pyright errors in touched files fixed at root cause
- [x] Pylance gate added to `.github/instructions/copilot.instructions.md`

## Gates

- [x] `task format`
- [x] `task test`
- [x] `pytest <changed modules> --cov=... --cov-report=term-missing` at 100%
- [x] `poetry run flake8 <changed modules> --max-line-length=120`
- [x] `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] `task lint-md`
- [x] No changed/new `*.py` file over 250 lines (fragment.py & text.py split)
- [ ] Remind to remove `TASK-realia-annotation-*.md` before merge
