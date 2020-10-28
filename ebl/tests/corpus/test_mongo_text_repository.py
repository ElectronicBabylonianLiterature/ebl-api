import attr
import pytest  # pyre-ignore

from ebl.corpus.application.text_serializer import serialize
from ebl.corpus.domain.text import TextId
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory, TextFactory

COLLECTION = "texts"
MANUSCRIPT_ID = 1
TEXT = TextFactory.build(  # pyre-ignore[16]
    chapters=(
        ChapterFactory.build(  # pyre-ignore[16]
            manuscripts=(
                # pyre-ignore[16]
                ManuscriptFactory.build(id=1, references=(ReferenceFactory.build(),)),
            )
        ),
    )
)


def when_text_in_collection(database, text=TEXT):
    database[COLLECTION].insert_one(serialize(text))


def test_creating_text(database, text_repository):
    text_repository.create(TEXT)

    inserted_text = database[COLLECTION].find_one(
        {"category": TEXT.category, "index": TEXT.index}, projection={"_id": False}
    )
    assert inserted_text == serialize(TEXT)


def test_it_is_not_possible_to_create_duplicates(text_repository):
    text_repository.create_indexes()
    text_repository.create(TEXT)

    with pytest.raises(DuplicateError):
        text_repository.create(TEXT)


def test_finding_text(database, text_repository):
    when_text_in_collection(database)

    assert text_repository.find(TEXT.id) == TEXT


def test_find_raises_exception_if_text_not_found(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.find(TextId(1, 1))


def test_listing_texts(database, text_repository):
    another_text = attr.evolve(TEXT, index=2)

    when_text_in_collection(database)
    when_text_in_collection(database, another_text)

    assert text_repository.list() == [TEXT, another_text]


def test_updating_text(database, text_repository):
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name="New Name")
    when_text_in_collection(database)

    text_repository.update(TEXT.id, updated_text)

    assert text_repository.find(updated_text.id) == updated_text


def test_updating_non_existing_text_raises_exception(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.update(TEXT.id, TEXT)
