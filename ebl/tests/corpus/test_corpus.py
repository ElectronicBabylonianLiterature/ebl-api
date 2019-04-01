import pydash
import pytest
from ebl.tests.factories.corpus import TextFactory
from ebl.errors import NotFoundError, DuplicateError


COLLECTION = 'texts'
TEXT = TextFactory.build()


def test_create(database, corpus):
    corpus.create(TEXT)

    result = database[COLLECTION].find_one({
        'category': TEXT.category,
        'index': TEXT.index
    })
    assert pydash.omit(result, '_id') == TEXT.to_dict()


def test_create_duplicate(corpus):
    corpus.create_indexes()
    corpus.create(TEXT)

    with pytest.raises(DuplicateError):
        corpus.create(TEXT)


def test_find(database, corpus):
    database[COLLECTION].insert_one(TEXT.to_dict())

    assert corpus.find(TEXT.category, TEXT.index) == TEXT


def test_find_not_found(corpus):
    with pytest.raises(NotFoundError):
        corpus.find(1, 1)
