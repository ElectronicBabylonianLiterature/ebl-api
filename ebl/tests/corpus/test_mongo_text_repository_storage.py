import attr

from ebl.corpus.application.schemas import ChapterSchema
from ebl.tests.corpus.test_mongo_text_repository import (
    CHAPTER,
    CHAPTER_SIGN_SCHEMA,
    CHAPTERS_COLLECTION,
)
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump

CHAPTER_UPDATE_FIELDS = [
    "manuscripts",
    "uncertain_fragments",
    "lines",
    "signs",
    "parser_version",
]


def find_stored_chapter(database) -> dict:
    return database[CHAPTERS_COLLECTION].find_one(
        {
            "textId.category": CHAPTER.text_id.category,
            "textId.index": CHAPTER.text_id.index,
            "stage": CHAPTER.stage.long_name,
            "name": CHAPTER.name,
        },
        projection={"_id": False},
    )


def test_creating_chapter(database, text_repository) -> None:
    text_repository.create_chapter(CHAPTER)

    assert find_stored_chapter(database) == stored_dump(ChapterSchema(), CHAPTER)


def test_created_chapter_omits_default_token_fields(database, text_repository):
    text_repository.create_chapter(CHAPTER)

    stored_chapter = find_stored_chapter(database)

    assert has_key(ChapterSchema().dump(CHAPTER), "erasure")
    assert not has_key(stored_chapter, "erasure")


def test_created_chapter_loads_back_unchanged(text_repository) -> None:
    text_repository.create_chapter(CHAPTER)

    assert text_repository.find_chapter(CHAPTER.id_) == CHAPTER


def test_updated_chapter_is_stored_sparse(database, text_repository) -> None:
    text_repository.create_chapter(CHAPTER)
    updated = attr.evolve(CHAPTER, signs=("KU",))

    text_repository.update(CHAPTER.id_, updated)

    stored_chapter = find_stored_chapter(database)
    expected = stored_dump(ChapterSchema(only=CHAPTER_UPDATE_FIELDS), updated)
    assert {key: stored_chapter[key] for key in expected} == expected
    assert text_repository.find_chapter(CHAPTER.id_) == updated


def test_sign_data_of_a_sparse_chapter_has_full_transliterations(text_repository):
    text_repository.create_chapter(CHAPTER)

    sign_data = text_repository.get_sign_data(CHAPTER.id_)

    assert sign_data == CHAPTER_SIGN_SCHEMA.dump(CHAPTER)
    assert has_key(sign_data["manuscripts"][0]["colophon"], "erasure")
