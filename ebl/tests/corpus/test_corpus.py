import attr
import pydash
import pytest
from ebl.tests.factories.corpus import TextFactory
from ebl.errors import NotFoundError, DuplicateError


COLLECTION = 'texts'
TEXT = TextFactory.build()


def test_creating_text(database, corpus):
    corpus.create(TEXT)

    result = database[COLLECTION].find_one({
        'category': TEXT.category,
        'index': TEXT.index
    })
    assert pydash.omit(result, '_id') == TEXT.to_dict()


def test_it_is_not_possible_to_create_duplicates(corpus):
    corpus.create_indexes()
    corpus.create(TEXT)

    with pytest.raises(DuplicateError):
        corpus.create(TEXT)


def test_finding_text(database, corpus):
    database[COLLECTION].insert_one(TEXT.to_dict())

    assert corpus.find(TEXT.category, TEXT.index) == TEXT


def test_find_raises_exception_if_text_not_found(corpus):
    with pytest.raises(NotFoundError):
        corpus.find(1, 1)


def test_updating_text(database, corpus):
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')

    database[COLLECTION].insert_one(TEXT.to_dict())
    result = corpus.update(TEXT.category, TEXT.index, updated_text)

    assert result == updated_text
    assert corpus.find(updated_text.category, updated_text.index) ==\
        updated_text


def test_updating_non_existing_text_raises_exception(corpus):
    with pytest.raises(NotFoundError):
        corpus.update(TEXT.category, TEXT.index, TEXT)
