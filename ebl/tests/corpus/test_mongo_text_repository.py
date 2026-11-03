import attr
import pytest

from ebl.corpus.application.schemas import TextSchema
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.text import UncertainFragment
from ebl.errors import DuplicateError, NotFoundError
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.tests.corpus.mongo_text_repository_fixtures import (
    CHAPTER,
    CHAPTERS_COLLECTION,
    TEXT,
    TEXTS_COLLECTION,
    UNCERTAIN_FRAGMENT,
    when_chapter_in_collection,
    when_text_in_collection,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.text_id import TextId


def test_creating_text(database, text_repository) -> None:
    text_repository.create(TEXT)

    inserted_text = database[TEXTS_COLLECTION].find_one(
        {"category": TEXT.category, "index": TEXT.index}, projection={"_id": False}
    )
    assert inserted_text == TextSchema(exclude=["chapters"]).dump(TEXT)


def test_it_is_not_possible_to_create_duplicate_texts(text_repository) -> None:
    text_repository.create_indexes()
    text_repository.create(TEXT)

    with pytest.raises(DuplicateError):
        text_repository.create(TEXT)


def test_it_is_not_possible_to_create_duplicate_chapters(text_repository) -> None:
    text_repository.create_indexes()
    text_repository.create(CHAPTER)

    with pytest.raises(DuplicateError):
        text_repository.create(CHAPTER)


def test_create_indexes_includes_query_indexes(database, text_repository) -> None:
    text_repository.create_indexes()

    text_index_keys = [
        index["key"]
        for index in database[TEXTS_COLLECTION].index_information().values()
    ]
    chapter_index_keys = [
        index["key"]
        for index in database[CHAPTERS_COLLECTION].index_information().values()
    ]

    assert [("genre", 1), ("category", 1), ("index", 1)] in text_index_keys
    assert [("category", 1)] in text_index_keys
    assert [("index", 1)] in text_index_keys
    assert [
        ("manuscripts.museumNumber.prefix", 1),
        ("manuscripts.museumNumber.number", 1),
        ("manuscripts.museumNumber.suffix", 1),
    ] in chapter_index_keys
    assert [
        ("uncertainFragments.prefix", 1),
        ("uncertainFragments.number", 1),
        ("uncertainFragments.suffix", 1),
    ] in chapter_index_keys


def test_finding_text(
    database, text_repository, bibliography_repository, fragment_repository
) -> None:
    text = attr.evolve(
        TEXT,
        chapters=(
            attr.evolve(
                TEXT.chapters[0],
                uncertain_fragments=(UncertainFragment(UNCERTAIN_FRAGMENT),),
            ),
        ),
    )
    chapter = attr.evolve(CHAPTER, uncertain_fragments=(UNCERTAIN_FRAGMENT,))
    when_text_in_collection(database, text)
    when_chapter_in_collection(database, chapter)
    fragment_repository.create(Fragment(UNCERTAIN_FRAGMENT))
    for reference in text.references:
        bibliography_repository.create(reference.document)

    assert text_repository.find(text.id) == text


def test_find_raises_exception_if_text_not_found(text_repository) -> None:
    with pytest.raises(NotFoundError):
        text_repository.find(TextId(Genre.LITERATURE, 1, 1))


def test_listing_texts(database, text_repository, bibliography_repository) -> None:
    another_text = attr.evolve(TEXT, index=999, name="Another text")
    another_chapter = attr.evolve(
        CHAPTER,
        text_id=another_text.id,
        stage=another_text.chapters[0].stage,
        name="Another chapter",
    )
    another_chapter_listing = attr.evolve(
        another_text.chapters[0],
        name="Another chapter",
    )
    another_text = attr.evolve(another_text, chapters=(another_chapter_listing,))
    when_text_in_collection(database)
    when_text_in_collection(database, another_text)
    when_chapter_in_collection(database)
    when_chapter_in_collection(database, another_chapter)
    for reference in TEXT.references:
        bibliography_repository.create(reference.document)

    assert text_repository.list() == [TEXT, another_text]


def test_finding_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.find_chapter(CHAPTER.id_) == CHAPTER


def test_finding_chapter_for_display(database, text_repository) -> None:
    when_text_in_collection(database)
    when_chapter_in_collection(database)

    assert text_repository.find_chapter_for_display(
        CHAPTER.id_
    ) == ChapterDisplay.of_chapter(TEXT, CHAPTER)


def test_finding_line(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.find_line(CHAPTER.id_, 0) == CHAPTER.lines[0]


def test_finding_line_not_found(database, text_repository) -> None:
    when_chapter_in_collection(database)

    with pytest.raises(NotFoundError):
        text_repository.find_line(CHAPTER.id_, len(CHAPTER.lines))


def test_finding_line_chapter_not_found(database, text_repository) -> None:
    with pytest.raises(NotFoundError):
        text_repository.find_line(CHAPTER.id_, 0)


def test_updating_chapter(database, text_repository) -> None:
    updated_chapter = attr.evolve(CHAPTER, lines=(), manuscripts=(), signs=())
    when_chapter_in_collection(database)

    text_repository.update(CHAPTER.id_, updated_chapter)

    assert text_repository.find_chapter(CHAPTER.id_) == updated_chapter


def test_updating_non_existing_chapter_raises_exception(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.update(CHAPTER.id_, CHAPTER)
