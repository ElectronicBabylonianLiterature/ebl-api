import mongomock
import pytest

from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_repository import MongoRepository


@pytest.fixture
def repository():
    return MongoRepository(mongomock.MongoClient().ebl, 'collection')


def test_create_and_find(repository):
    document = {'data': 'payload'}
    insert_id = repository.create(document)

    assert repository.find(insert_id) == document


def test_create_dulicate(repository):
    document = {'_id': 'ID', 'data': 'payload'}
    repository.create(document)

    with pytest.raises(DuplicateError):
        repository.create(document)


def test_document_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.find('unknown id')
