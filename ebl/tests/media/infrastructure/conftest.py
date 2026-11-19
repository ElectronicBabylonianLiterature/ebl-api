import pytest
from pymongo.database import Database

from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository


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
