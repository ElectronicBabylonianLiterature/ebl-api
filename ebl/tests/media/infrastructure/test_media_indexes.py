from pymongo.database import Database

from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.media_indexes import (
    MEDIA_REQUIRED_INDEXES,
    MEDIA_REPOSITORY_INDEXES,
    MEDIA_STORE_INDEXES,
    create_media_indexes,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository


def test_preparation_matches_shared_index_definitions(media_database: Database) -> None:
    MongoMediaRepository(media_database).create_indexes()
    GridFsMediaRepresentationStore(media_database).create_indexes()
    create_media_indexes(media_database, MEDIA_REQUIRED_INDEXES)
    for definition in MEDIA_REQUIRED_INDEXES:
        indexes = media_database[definition.collection].index_information()
        information = indexes[definition.name]
        assert information["key"] == list(definition.keys)
        assert information.get("unique", definition.implicit) == definition.unique
        assert not information.get("sparse", False)
        assert not information.get("hidden", False)
        assert "partialFilterExpression" not in information
        assert information.get("collation", {}).get("locale", "simple") == "simple"
    assert len(MEDIA_REQUIRED_INDEXES) == 12
    assert {item.collection for item in MEDIA_REQUIRED_INDEXES if item.implicit} == {
        "media",
        "mediaSources",
        "mediaLocks",
        "mediaFiles",
        "media.files",
        "media.chunks",
    }


def test_explicit_indexes_override_collection_collation(
    media_database: Database,
) -> None:
    definitions = (*MEDIA_REPOSITORY_INDEXES, *MEDIA_STORE_INDEXES)
    for collection in {item.collection for item in definitions}:
        media_database.create_collection(collection, collation={"locale": "en"})
    MongoMediaRepository(media_database).create_indexes()
    GridFsMediaRepresentationStore(media_database).create_indexes()
    for definition in definitions:
        information = media_database[definition.collection].index_information()[
            definition.name
        ]
        assert information.get("collation", {}).get("locale", "simple") == "simple"
