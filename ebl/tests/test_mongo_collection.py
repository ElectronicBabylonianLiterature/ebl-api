import datetime

import pytest
from bson import ObjectId

from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection


@pytest.fixture
def collection(database):
    return MongoCollection(database, "collection")


def test_create_many_and_find_by_id(collection):
    documents = [{"data": "payload-1"}, {"data": "payload-2"}]

    insert_ids = collection.insert_many(documents)
    assert [
        collection.find_one_by_id(insert_id) for insert_id in insert_ids
    ] == documents


def test_create_and_find_by_id(collection):
    document = {"data": "payload"}
    insert_id = collection.insert_one(document)

    assert collection.find_one_by_id(insert_id) == document


def test_create_duplicate(collection):
    document = {"_id": "ID", "data": "payload"}
    collection.insert_one(document)

    with pytest.raises(DuplicateError):
        collection.insert_one(document)


def test_find_by_id_document_not_found(collection):
    with pytest.raises(NotFoundError):
        collection.find_one_by_id("unknown id")


def test_find(collection):
    document = {"data": "payload"}
    collection.insert_one(document)

    assert collection.find_one({"data": "payload"}) == document


def test_exists(collection):
    document = {"data": "payload"}
    collection.insert_one(document)

    assert collection.exists({"data": "payload"}) is True


def test_delete(collection):
    document = {"data": "payload"}
    collection.insert_one(document)

    collection.delete_one({"data": "payload"})
    assert collection.exists({"data": "payload"}) is False


def test_delete_not_found(collection):
    document = {"data": "payload"}
    collection.insert_one(document)

    with pytest.raises(NotFoundError):
        collection.delete_one({"data": "payload1"})


def test_find_document_not_found(collection):
    with pytest.raises(NotFoundError):
        collection.find_one({})


def test_find_many(collection):
    document_match1 = {"data": "payload"}
    document_match2 = {"data": "payload"}
    document_no_match = {"data": "another payload"}
    collection.insert_one(document_match1)
    collection.insert_one(document_match2)
    collection.insert_one(document_no_match)

    assert list(collection.find_many({"data": "payload"})) == [
        document_match1,
        document_match2,
    ]


def test_find_many_document_not_found(collection):
    assert not list(collection.find_many({}))


def test_aggregate(collection):
    document_match1 = {"data": "payload"}
    document_match2 = {"data": "payload"}
    document_no_match = {"data": "another payload"}
    collection.insert_one(document_match1)
    collection.insert_one(document_match2)
    collection.insert_one(document_no_match)

    assert list(collection.aggregate([{"$match": {"data": "payload"}}])) == [
        document_match1,
        document_match2,
    ]


def test_update(collection):
    document = {"data": "payload"}
    insert_id = collection.insert_one(document)
    collection.update_one({"_id": insert_id}, {"$set": {"data": "updated payload"}})
    assert collection.find_one_by_id(insert_id) == {
        "_id": insert_id,
        "data": "updated payload",
    }


def test_update_many(collection):
    documents = [{"data": "payload"}, {"data": "payload2"}]
    insert_ids = collection.insert_many(documents)
    collection.update_many({}, {"$set": {"data": "updated payload"}})

    assert [collection.find_one_by_id(_id) for _id in insert_ids] == [
        {
            "_id": _id,
            "data": "updated payload",
        }
        for _id in insert_ids
    ]


def test_update_document_not_found(collection):
    with pytest.raises(NotFoundError):
        collection.update_one({}, {"$set": {"data": "not found"}})


def test_replace(collection):
    document = {"data": "payload"}
    insert_id = collection.insert_one(document)
    replacement = {"_id": insert_id, "newData": "payload"}
    collection.replace_one(replacement)
    assert collection.find_one_by_id(insert_id) == replacement


def test_replace_document_not_found(collection):
    with pytest.raises(NotFoundError):
        collection.replace_one({"_id": "unknown id"})


def test_count(collection):
    collection.insert_one({"data": "payload"})
    collection.insert_one({"data": "payload"})
    collection.insert_one({"data": "another payload"})

    assert collection.count_documents({"data": "payload"}) == 2


def test_get_all_values_ignores_object_ids(collection) -> None:
    object_id = ObjectId()
    collection.insert_one({"data": object_id})
    collection.insert_one({"data": "value"})

    assert collection.get_all_values("data") == ["value"]


def test_unicode_and_datetime_roundtrip(collection) -> None:
    timestamp = datetime.datetime(2023, 7, 12, 10, 11, 12)
    document = {"data": "šà-ḫa", "created": timestamp}

    insert_id = collection.insert_one(document)
    stored = collection.find_one_by_id(insert_id)

    assert stored == {"_id": insert_id, "data": "šà-ḫa", "created": timestamp}
