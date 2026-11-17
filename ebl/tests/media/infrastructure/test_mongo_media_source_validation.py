import pytest
from pymongo.database import Database

from ebl.media.domain import MediaImportSource
from ebl.media.infrastructure.media_documents import stored_document
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import copy_media, photo_media, stored_media


def imported_document() -> dict:
    return stored_document(
        stored_media(
            photo_media(
                import_source=MediaImportSource("gridfs", "one", container="photos")
            )
        )
    )


def assert_invalid_source_prevents_setup(
    database: Database, document: dict, message: str
) -> None:
    database.media.insert_one(document)
    if "sourceKey" in document:
        database.mediaSources.insert_one(
            {"_id": document["sourceKey"], "mediaId": document["_id"]}
        )
    collections_before = database.list_collection_names()
    indexes_before = database.media.index_information()
    with pytest.raises(ValueError, match=message):
        MongoMediaRepository(database).create_indexes()
    assert database.list_collection_names() == collections_before
    assert database.media.index_information() == indexes_before


@pytest.mark.parametrize("missing", ["importSource", "sourceKey"])
def test_source_and_key_must_both_exist(media_database: Database, missing: str) -> None:
    document = imported_document()
    del document[missing]
    assert_invalid_source_prevents_setup(media_database, document, "sourceKey")


def test_matching_reservation_cannot_hide_incorrect_key(
    media_database: Database,
) -> None:
    document = imported_document()
    document["sourceKey"] = "incorrect"
    assert_invalid_source_prevents_setup(media_database, document, "sourceKey")


@pytest.mark.parametrize("missing", ["system", "fileId", "container"])
def test_incomplete_source_prevents_setup(
    media_database: Database, missing: str
) -> None:
    document = imported_document()
    del document["importSource"][missing]
    assert_invalid_source_prevents_setup(
        media_database, document, "invalid importSource"
    )


def test_null_source_prevents_setup(media_database: Database) -> None:
    document = imported_document()
    document["importSource"] = None
    assert_invalid_source_prevents_setup(
        media_database, document, "invalid importSource"
    )


def test_invalid_source_identity_prevents_setup(media_database: Database) -> None:
    document = imported_document()
    document["importSource"]["fileId"] = ""
    assert_invalid_source_prevents_setup(
        media_database, document, "invalid importSource"
    )


def test_source_validation_accepts_active_unsourced_and_deleted_records(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    imported = stored_media(
        photo_media(import_source=MediaImportSource("gridfs", "one"))
    )
    mongo_media_repository.create(imported)
    mongo_media_repository.create(stored_media(copy_media()))
    mongo_media_repository.create_indexes()
    mongo_media_repository.delete(imported.media.id)
    mongo_media_repository.create_indexes()
