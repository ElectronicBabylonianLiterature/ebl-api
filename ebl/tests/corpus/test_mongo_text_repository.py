import attr
import pytest

from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    TextFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.text_id import TextId


TEXTS_COLLECTION = "texts"
CHAPTERS_COLLECTION = "chapters"
MANUSCRIPT_ID = 1
TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(ManuscriptFactory.build(id=1, references=tuple()),),
    lines=(
        LineFactory.build(manuscript_id=1, translation=TEXT.chapters[0].translation),
    ),
)


def when_text_in_collection(database, text=TEXT):
    database[TEXTS_COLLECTION].insert_one(TextSchema(exclude=["chapters"]).dump(text))


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


def test_finding_text(database, text_repository, bibliography_repository):
    when_text_in_collection(database)
    when_chapter_in_collection(database)
    for reference in TEXT.references:
        bibliography_repository.create(reference.document)

    assert text_repository.find(TEXT.id) == TEXT


def test_find_raises_exception_if_text_not_found(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.find(TextId(Genre.LITERATURE, 1, 1))


def test_listing_texts(database, text_repository, bibliography_repository):
    another_text = attr.evolve(TEXT, index=2)
    another_chapter = attr.evolve(
        CHAPTER,
        text_id=another_text.id,
        stage=another_text.chapters[0].stage,
        name=another_text.chapters[0].name,
    )

    when_text_in_collection(database)
    when_text_in_collection(database, another_text)
    when_chapter_in_collection(database)
    when_chapter_in_collection(database, another_chapter)
    for reference in TEXT.references:
        bibliography_repository.create(reference.document)

    assert text_repository.list() == [TEXT, another_text]


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


def test_query_manuscripts_by_chapter(database, text_repository):
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_) == list(
        CHAPTER.manuscripts
    )


def test_query_manuscripts_by_chapter_not_found(database, text_repository):
    with pytest.raises(NotFoundError):
        assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_)
