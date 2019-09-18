import mongomock
import pytest

from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_repository import MongoRepository


class TestableRepository(MongoRepository):
    def __init__(self, database, collection):
        super().__init__(database, collection)

    def create(self, document):
        return super()._insert_one(document)

    def find_by_id(self, id_):
        return super()._find_one_by_id(id_)

    def find(self, query):
        return super()._find_one(query)

    def find_many(self, query):
        return super()._find_many(query)

    def aggregate(self, pipeline):
        return super()._aggregate(pipeline)

    def replace(self, document):
        return super()._replace_one(document)

    def update(self, id_, update):
        return super()._update_one({'_id': id_}, update)

    def count(self, query):
        return super()._count_documents(query)


@pytest.fixture
def repository():
    return TestableRepository(mongomock.MongoClient().ebl, 'collection')


def test_create_and_find_by_id(repository):
    document = {'data': 'payload'}
    insert_id = repository.create(document)

    assert repository.find_by_id(insert_id) == document


def test_create_duplicate(repository):
    document = {'_id': 'ID', 'data': 'payload'}
    repository.create(document)

    with pytest.raises(DuplicateError):
        repository.create(document)


def test_find_by_id_document_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.find_by_id('unknown id')


def test_find(repository):
    document = {'data': 'payload'}
    repository.create(document)

    assert repository.find({'data': 'payload'}) == document


def test_find_document_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.find({})


def test_find_many(repository):
    document_match1 = {'data': 'payload'}
    document_match2 = {'data': 'payload'}
    document_no_match = {'data': 'another payload'}
    repository.create(document_match1)
    repository.create(document_match2)
    repository.create(document_no_match)

    assert [
        document
        for document
        in repository.find_many({'data': 'payload'})
    ] == [
        document_match1, document_match2
    ]


def test_find_many_document_not_found(repository):
    assert repository.find_many({}).count() == 0


def test_aggregate(repository):
    document_match1 = {'data': 'payload'}
    document_match2 = {'data': 'payload'}
    document_no_match = {'data': 'another payload'}
    repository.create(document_match1)
    repository.create(document_match2)
    repository.create(document_no_match)

    assert [
        document
        for document
        in repository.aggregate([{
          '$match': {'data': 'payload'}
        }])
    ] == [
        document_match1, document_match2
    ]


def test_update(repository):
    document = {'data': 'payload'}
    insert_id = repository.create(document)
    repository.update(insert_id, {
        '$set': {'data': 'updated payload'}
    })
    assert repository.find(insert_id) == {
        '_id': insert_id,
        'data': 'updated payload'
    }


def test_update_document_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.update('unknown id', {'$set': {'data': 'not found'}})


def test_replace(repository):
    document = {'data': 'payload'}
    insert_id = repository.create(document)
    replacement = {'_id': insert_id, 'newData': 'payload'}
    repository._replace_one(replacement)
    assert repository.find(insert_id) == replacement


def test_replace_document_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.replace({'_id': 'unknown id'})


def test_count(repository):
    repository.create({'data': 'payload'})
    repository.create({'data': 'payload'})
    repository.create({'data': 'another payload'})

    assert repository.count({'data': 'payload'}) == 2
