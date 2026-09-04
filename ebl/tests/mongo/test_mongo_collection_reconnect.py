from unittest.mock import Mock

import pytest
from pymongo.errors import AutoReconnect, DuplicateKeyError


def test_insert_one_retries_once_on_auto_reconnect(collection) -> None:
    document = {"data": "payload"}

    insert_result = Mock()
    insert_result.inserted_id = "inserted-id"

    mocked_collection = Mock()
    mocked_collection.insert_one.side_effect = [
        AutoReconnect("operation cancelled"),
        insert_result,
    ]

    collection._MongoCollection__get_collection = lambda: mocked_collection

    assert collection.insert_one(document) == "inserted-id"
    assert mocked_collection.insert_one.call_count == 2


def test_insert_one_reraises_auto_reconnect_after_last_attempt(collection) -> None:
    document = {"data": "payload"}

    mocked_collection = Mock()
    mocked_collection.insert_one.side_effect = [
        AutoReconnect("operation cancelled"),
        AutoReconnect("operation cancelled"),
    ]

    collection._MongoCollection__get_collection = lambda: mocked_collection

    with pytest.raises(AutoReconnect):
        collection.insert_one(document)

    assert mocked_collection.insert_one.call_count == 2


def test_insert_one_duplicate_after_auto_reconnect_returns_document_id(
    collection,
) -> None:
    document = {"_id": "fixed-id", "data": "payload"}

    mocked_collection = Mock()
    mocked_collection.insert_one.side_effect = [
        AutoReconnect("operation cancelled"),
        DuplicateKeyError("duplicate"),
    ]

    collection._MongoCollection__get_collection = lambda: mocked_collection

    assert collection.insert_one(document) == "fixed-id"
    assert mocked_collection.insert_one.call_count == 2


def test_update_one_retries_once_on_auto_reconnect(collection) -> None:
    update_result = Mock()
    update_result.matched_count = 1

    mocked_collection = Mock()
    mocked_collection.update_one.side_effect = [
        AutoReconnect("operation cancelled"),
        update_result,
    ]

    collection._MongoCollection__get_collection = lambda: mocked_collection

    assert (
        collection.update_one({"_id": "id"}, {"$set": {"data": "x"}}) is update_result
    )
    assert mocked_collection.update_one.call_count == 2


def test_update_one_reraises_auto_reconnect_after_last_attempt(collection) -> None:
    mocked_collection = Mock()
    mocked_collection.update_one.side_effect = [
        AutoReconnect("operation cancelled"),
        AutoReconnect("operation cancelled"),
    ]

    collection._MongoCollection__get_collection = lambda: mocked_collection

    with pytest.raises(AutoReconnect):
        collection.update_one({"_id": "id"}, {"$set": {"data": "x"}})

    assert mocked_collection.update_one.call_count == 2
