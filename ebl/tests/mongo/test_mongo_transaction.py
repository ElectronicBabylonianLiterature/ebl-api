from contextlib import contextmanager
from typing import Iterator
from unittest.mock import Mock

import pytest
from pymongo.client_session import ClientSession
from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.mongo_transaction import run_in_transaction, supports_transactions
from ebl.tests import mongo_replica_set


def client_answering(hello: dict) -> Mock:
    client = Mock()
    client.admin.command.return_value = hello
    return client


@pytest.mark.parametrize(
    "hello,expected",
    [
        ({"setName": "rs-ebl"}, True),
        ({"msg": "isdbgrid"}, True),
        ({"isWritablePrimary": True}, False),
    ],
)
def test_supports_transactions(hello: dict, expected: bool) -> None:
    assert supports_transactions(client_answering(hello)) is expected


def test_transactional_client_reuses_replica_set_client() -> None:
    client = client_answering({"setName": "rs-ebl"})
    with mongo_replica_set.transactional_client(client) as transactional:
        assert transactional is client


def test_transactional_client_starts_replica_set_for_standalone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replica_set = Mock()

    @contextmanager
    def fake_replica_set_client() -> Iterator[Mock]:
        yield replica_set

    monkeypatch.setattr(
        mongo_replica_set, "replica_set_client", fake_replica_set_client
    )
    standalone = client_answering({"isWritablePrimary": True})
    with mongo_replica_set.transactional_client(standalone) as transactional:
        assert transactional is replica_set


def test_transaction_commits(transactional_database: Database) -> None:
    collection = MongoCollection(transactional_database, "records")

    def insert(session: ClientSession) -> str:
        collection.insert_one({"_id": "committed"}, session=session)
        assert collection.count_documents({}) == 0
        return "result"

    result = run_in_transaction(transactional_database.client, insert)

    assert result == "result"
    assert collection.find_one_by_id("committed") == {"_id": "committed"}


def test_transaction_aborts_on_error(transactional_database: Database) -> None:
    collection = MongoCollection(transactional_database, "records")
    collection.insert_one({"_id": "kept", "value": 1})

    def change_then_fail(session: ClientSession) -> None:
        collection.update_one_by_id("kept", {"$set": {"value": 2}}, session)
        collection.insert_one({"_id": "aborted"}, session=session)
        raise ValueError("Failed")

    with pytest.raises(ValueError, match="Failed"):
        run_in_transaction(transactional_database.client, change_then_fail)

    assert collection.count_documents({}) == 1
    assert collection.find_one_by_id("kept") == {"_id": "kept", "value": 1}
