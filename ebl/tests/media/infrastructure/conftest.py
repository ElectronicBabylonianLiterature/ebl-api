from collections.abc import Iterator
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.database import Database

from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.infrastructure.replica_set import replica_set_client


@pytest.fixture(scope="session")
def media_mongo_client(mongo_client: MongoClient) -> Iterator[MongoClient]:
    topology = mongo_client.admin.command("hello")
    if topology.get("setName") or topology.get("msg") == "isdbgrid":
        yield mongo_client
    else:
        with replica_set_client() as client:
            yield client


@pytest.fixture
def media_database(media_mongo_client: MongoClient) -> Iterator[Database]:
    database = media_mongo_client[f"media_test_{uuid4().hex}"]
    yield database
    media_mongo_client.drop_database(database.name)


@pytest.fixture
def mongo_media_repository(media_database: Database) -> MongoMediaRepository:
    repository = MongoMediaRepository(media_database)
    repository.create_indexes()
    return repository


@pytest.fixture
def representation_store(media_database: Database) -> GridFsMediaRepresentationStore:
    store = GridFsMediaRepresentationStore(media_database)
    store.create_indexes()
    return store
