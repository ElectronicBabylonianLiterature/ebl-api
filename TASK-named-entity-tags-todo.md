# TASK-named-entity-tags-todo

Separate proper-noun (named-entity) tags from part-of-speech in the dictionary.

## Code changes

- [x] `WordSchema`: add `namedEntityTags` list field (default empty list).
- [x] `ProperNounCreationRequestSchema`: replace `pos` with `namedEntityTags`.
- [x] `WordRepository.create_proper_noun` (abstract): rename param to
      `named_entity_tags`.
- [x] `MongoWordRepository.create_proper_noun`: write `pos: []` and
      `namedEntityTags`.
- [x] `Dictionary.create_proper_noun`: rename param, pass through.
- [x] `words.py` `on_post`: read `namedEntityTags` from request.
- [x] `words.py` `_is_valid_created_word_payload`: validate `namedEntityTags`.

## Audit

- [x] `corpus/domain/dictionary_display.py`, `dictionary_line.py`: confirm no
      `pos` surfacing (none found).
- [x] `atf_importer` `pos`: confirm it is source-glossary POS, unrelated to
      word docs (no named-entity codes written to word `pos`).

## Migration

- [x] Idempotent migration moving the 16 named-entity codes out of `pos` into
      `namedEntityTags`, backfilling `[]` everywhere, with dry-run + logging.
- [x] Tests for the migration.

## Tests

- [x] `test_word_schema.py`: round-trip includes `namedEntityTags`.
- [x] `test_create_proper_noun.py`: request/created doc use `namedEntityTags`.
- [x] `test_words_route.py` / fixtures: add `namedEntityTags`.
- [x] `word` fixture in `conftest.py`: add `namedEntityTags`.
- [x] Full suite green; 100% coverage on touched lines.

## Cleanup

- [ ] Remove TASK-*.md files before PR merge.
