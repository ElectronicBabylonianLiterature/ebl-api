from unittest.mock import Mock

import pytest
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import AutoReconnect

from ebl.mongo_collection import MongoCollection, retries_on_reconnect

SEEDED = [{"_id": "one", "value": 1}, {"_id": "two", "value": 2}]


def write_everything(collection: MongoCollection, session: ClientSession) -> None:
    collection.insert_one({"_id": "three", "value": 3}, session=session)
    collection.insert_many([{"_id": "four"}, {"_id": "five"}], session=session)
    collection.replace_one({"_id": "one", "value": 10}, session=session)
    collection.update_one({"_id": "two"}, {"$set": {"value": 20}}, session=session)
    collection.update_one_by_id("three", {"$set": {"value": 30}}, session=session)
    collection.delete_one({"_id": "four"}, session=session)
    collection.delete_many({"_id": "five"}, session=session)


def test_every_method_uses_the_session(transactional_database: Database) -> None:
    collection = MongoCollection(transactional_database, "records")
    collection.insert_many(SEEDED)

    with transactional_database.client.start_session() as session:
        session.start_transaction()
        write_everything(collection, session)

        assert collection.count_documents({}, session=session) == 3
        assert collection.find_one_by_id("one", session=session)["value"] == 10
        assert collection.find_one({"_id": "two"}, session=session)["value"] == 20
        assert collection.exists({"value": 30}, session=session)
        assert not collection.exists({"value": 30})
        session.abort_transaction()

    assert list(collection.find_many({}).sort("_id")) == SEEDED


@pytest.mark.parametrize(
    "session,expected",
    [
        (None, True),
        (Mock(in_transaction=False), True),
        (Mock(in_transaction=True), False),
    ],
)
def test_retries_on_reconnect(session, expected: bool) -> None:
    assert retries_on_reconnect(session) is expected


@pytest.mark.parametrize("method", ["insert_one", "update_one"])
def test_no_retry_inside_transaction(collection, method: str) -> None:
    mocked_collection = Mock()
    getattr(mocked_collection, method).side_effect = AutoReconnect("cancelled")
    collection._MongoCollection__get_collection = lambda: mocked_collection
    session = Mock(in_transaction=True)
    arguments = ({"_id": "id"},) if method == "insert_one" else ({}, {"$set": {}})

    with pytest.raises(AutoReconnect):
        getattr(collection, method)(*arguments, session=session)

    assert getattr(mocked_collection, method).call_count == 1
