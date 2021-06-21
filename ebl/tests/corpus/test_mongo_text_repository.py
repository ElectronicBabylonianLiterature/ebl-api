import attr
import pytest

from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory, TextFactory
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


TEXTS_COLLECTION = "texts"
CHAPTERS_COLLECTION = "chapters"
MANUSCRIPT_ID = 1
TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(ManuscriptFactory.build(id=1, references=tuple()),),
)


def when_chapter_in_collection(database, chapter=CHAPTER):
    database[CHAPTERS_COLLECTION].insert_one(ChapterSchema().dump(chapter))


def test_creating_text(database, text_repository):
    text_repository.create(TEXT)

    inserted_text = database[TEXTS_COLLECTION].find_one(
        {"category": TEXT.category, "index": TEXT.index}, projection={"_id": False}
    )
    assert inserted_text == TextSchema(exclude=["chapters"]).dump(TEXT)


def test_creating_chapter(database, text_repository):
    text_repository.create_chapter(CHAPTER)

    inserted_chapter = database[CHAPTERS_COLLECTION].find_one(
        {
            "textId.category": CHAPTER.text_id.category,
            "textId.index": CHAPTER.text_id.index,
            "stage": CHAPTER.stage.value,
            "name": CHAPTER.name,
        },
        projection={"_id": False},
    )
    assert inserted_chapter == ChapterSchema().dump(CHAPTER)


def test_it_is_not_possible_to_create_duplicate_texts(text_repository):
    text_repository.create_indexes()
    text_repository.create(TEXT)

    with pytest.raises(DuplicateError):
        text_repository.create(TEXT)


def test_it_is_not_possible_to_create_duplicate_chapters(text_repository):
    text_repository.create_indexes()
    text_repository.create(CHAPTER)

    with pytest.raises(DuplicateError):
        text_repository.create(CHAPTER)


def test_updating_chapter(database, text_repository):
    updated_chapter = attr.evolve(
        CHAPTER, lines=tuple(), manuscripts=tuple(), signs=tuple()
    )
    when_chapter_in_collection(database)

    text_repository.update(CHAPTER.id_, updated_chapter)

    assert text_repository.find_chapter(CHAPTER.id_) == updated_chapter


def test_updating_non_existing_chapter_raises_exception(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.update(CHAPTER.id_, CHAPTER)


@pytest.mark.parametrize(
    "signs,is_match",
    [([["KU"]], True), ([["ABZ075"], ["KU"]], True), ([["UD"]], False)],
)
def test_query_by_transliteration(signs, is_match, text_repository):
    text_repository.create_chapter(CHAPTER)

    result = text_repository.query_by_transliteration(TransliterationQuery(signs))
    expected = [CHAPTER] if is_match else []
    assert result == expected
