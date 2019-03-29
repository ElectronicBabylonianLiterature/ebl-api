import pydash
import pytest
from ebl.errors import NotFoundError, DuplicateError


COLLECTION = 'texts'
TEXT = {
    'category': 1,
    'index': 3,
    'name': 'Palm & Vine',
    'chapters': [
        {
            'classification': 'Ancient',
            'period': 'Neo-Babylonian',
            'number': 1
        }
    ]
}


def test_create(database, text, corpus):
    corpus.create(text)

    result = database[COLLECTION].find_one({'category': 1, 'index': 3})
    assert pydash.omit(result, '_id') == TEXT


def test_create_duplicate(corpus, text):
    corpus.create_indexes()
    corpus.create(text)

    with pytest.raises(DuplicateError):
        corpus.create(text)


def test_find(database, corpus, text):
    database[COLLECTION].insert_one(TEXT)

    assert corpus.find(1, 3) == text


def test_find_not_found(corpus):
    with pytest.raises(NotFoundError):
        corpus.find(1, 1)
