import pytest

from ebl.mongo_collection import MongoCollection


@pytest.fixture
def collection(database):
    return MongoCollection(database, "collection")
