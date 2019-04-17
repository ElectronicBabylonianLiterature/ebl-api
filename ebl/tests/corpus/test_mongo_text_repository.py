import attr
import pytest

from ebl.corpus.text import TextId
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (ChapterFactory, ManuscriptFactory,
                                        TextFactory)

COLLECTION = 'texts'
TEXT = TextFactory.build(
    chapters=(ChapterFactory.build(
        manuscripts=(ManuscriptFactory.build(
            references=(ReferenceFactory.build(),)
        ),)
    ),)
)


def when_text_in_collection(database):
    database[COLLECTION].insert_one(TEXT.to_dict())


def test_creating_text(database, text_repository):
    text_repository.create(TEXT)

    inserted_text = database[COLLECTION].find_one({
        'category': TEXT.category,
        'index': TEXT.index
    }, projection={'_id': False})
    assert inserted_text == TEXT.to_dict()


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


def test_updating_text(database, text_repository):
    # pylint: disable=R0913
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    when_text_in_collection(database)

    result = text_repository.update(TEXT.id, updated_text)

    assert result == updated_text
    assert text_repository.find(updated_text.id) == updated_text


def test_updating_non_existing_text_raises_exception(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.update(TEXT.id, TEXT)
