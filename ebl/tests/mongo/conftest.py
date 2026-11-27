from typing import Iterator
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.tests.mongo_replica_set import transactional_client


@pytest.fixture
def collection(database):
    return MongoCollection(database, "collection")


@pytest.fixture(scope="session")
def transactional_mongo_client(mongo_client: MongoClient) -> Iterator[MongoClient]:
    with transactional_client(mongo_client) as client:
        yield client


@pytest.fixture
def transactional_database(
    transactional_mongo_client: MongoClient,
) -> Iterator[Database]:
    database = transactional_mongo_client[f"transaction_test_{uuid4().hex}"]
    yield database
    transactional_mongo_client.drop_database(database.name)
