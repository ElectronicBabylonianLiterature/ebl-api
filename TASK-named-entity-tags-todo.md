# TASK-named-entity-tags-todo

Separate proper-noun (named-entity) tags from part-of-speech in the dictionary.

## Code changes

- [ ] `WordSchema`: add `namedEntityTags` list field (default empty list).
- [ ] `ProperNounCreationRequestSchema`: replace `pos` with `namedEntityTags`.
- [ ] `WordRepository.create_proper_noun` (abstract): rename param to
      `named_entity_tags`.
- [ ] `MongoWordRepository.create_proper_noun`: write `pos: []` and
      `namedEntityTags`.
- [ ] `Dictionary.create_proper_noun`: rename param, pass through.
- [ ] `words.py` `on_post`: read `namedEntityTags` from request.
- [ ] `words.py` `_is_valid_created_word_payload`: validate `namedEntityTags`.

## Audit

- [ ] `corpus/domain/dictionary_display.py`, `dictionary_line.py`: confirm no
      `pos` surfacing (none found).
- [ ] `atf_importer` `pos`: confirm it is source-glossary POS, unrelated to
      word docs (no named-entity codes written to word `pos`).

## Migration

- [ ] Idempotent migration moving the 16 named-entity codes out of `pos` into
      `namedEntityTags`, backfilling `[]` everywhere, with dry-run + logging.
- [ ] Tests for the migration.

## Tests

- [ ] `test_word_schema.py`: round-trip includes `namedEntityTags`.
- [ ] `test_create_proper_noun.py`: request/created doc use `namedEntityTags`.
- [ ] `test_words_route.py` / fixtures: add `namedEntityTags`.
- [ ] `word` fixture in `conftest.py`: add `namedEntityTags`.
- [ ] Full suite green; 100% coverage on touched lines.

## Cleanup

- [ ] Remove TASK-*.md files before PR merge.
