from typing import Callable, Iterator, List, Sequence
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.database import Database

from ebl.media.application import (
    MediaRepository,
    MediaRepresentationStore,
    StoredMedia,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.tests.media.infrastructure.replica_set import replica_set_client

MediaRepositoryFactory = Callable[[Sequence[StoredMedia]], MediaRepository]
RepresentationStoreFactory = Callable[[], MediaRepresentationStore]


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
def call_log() -> List[str]:
    return []


@pytest.fixture
def media_repository_factory(call_log: List[str]) -> MediaRepositoryFactory:
    """Build a repository under test.

    Contract tests depend on this fixture rather than on a concrete class, so a
    future Mongo adapter can reuse the same contract modules by overriding the
    fixture in its own conftest.
    """

    def factory(media: Sequence[StoredMedia] = ()) -> MediaRepository:
        return InMemoryMediaRepository(media, call_log)

    return factory


@pytest.fixture
def representation_store_factory(call_log: List[str]) -> RepresentationStoreFactory:
    """Build a representation store under test. See `media_repository_factory`."""

    def factory() -> MediaRepresentationStore:
        return InMemoryRepresentationStore(call_log)

    return factory
