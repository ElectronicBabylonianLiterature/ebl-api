from typing import Any

import attr
import pytest
from pymongo.database import Database

from ebl.media.domain import MediaId, MediaType
from ebl.media.infrastructure.mongo_media_repository import (
    COLLECTION,
    MongoMediaRepository,
)
from ebl.tests.media.factories import media_import_source, photo_media, stored_media
from ebl.transliteration.domain.museum_number import MuseumNumber

K1 = MuseumNumber.of("K.1")


@pytest.fixture
def repository(database: Database) -> MongoMediaRepository:
    return MongoMediaRepository(database)


def _stored(**kwargs: Any):
    return stored_media(photo_media(**kwargs))


def test_document_uses_the_media_id_as_mongo_id(
    repository: MongoMediaRepository, database: Database
) -> None:
    stored = _stored()
    repository.create(stored)
    document = database[COLLECTION].find_one({})

    assert document is not None
    assert document["_id"] == str(stored.media.id)


def test_document_persists_the_documented_field_names(
    repository: MongoMediaRepository, database: Database
) -> None:
    repository.create(
        _stored(
            caption="Obverse",
            attribution="The British Museum",
            import_source=media_import_source(),
        )
    )
    document = database[COLLECTION].find_one({})

    assert document is not None
    assert document["type"] == MediaType.PHOTO.value
    assert document["originalFilename"] == "BM-12345-obverse.jpg"
    assert document["caption"] == "Obverse"
    assert document["attribution"] == "The British Museum"
    assert document["associations"][0]["fragmentId"] == str(K1)
    assert document["associations"][0]["sortOrder"] == 0
    assert document["associations"][0]["isPrimary"] is True
    assert document["representations"]["original"]["mimeType"] == "image/jpeg"
    assert document["representations"]["original"]["fileSize"] == 5242880


def test_document_omits_absent_optional_metadata(
    repository: MongoMediaRepository, database: Database
) -> None:
    repository.create(_stored(caption=None, attribution=None, import_source=None))
    document = database[COLLECTION].find_one({})

    assert document is not None
    assert "caption" not in document
    assert "attribution" not in document
    assert "importSource" not in document


def test_document_persists_import_source_container_not_bucket(
    repository: MongoMediaRepository, database: Database
) -> None:
    repository.create(_stored(import_source=media_import_source(container="photos")))
    document = database[COLLECTION].find_one({})

    assert document is not None
    assert document["importSource"] == {
        "system": "legacy-gridfs",
        "fileId": "legacy-gridfs-id",
        "container": "photos",
    }
    assert "bucket" not in document["importSource"]


def test_document_omits_an_absent_import_source_container(
    repository: MongoMediaRepository, database: Database
) -> None:
    repository.create(_stored(import_source=media_import_source(container=None)))
    document = database[COLLECTION].find_one({})

    assert document is not None
    assert "container" not in document["importSource"]


def test_finds_media_by_full_import_source_identity(
    repository: MongoMediaRepository,
) -> None:
    stored = _stored(import_source=media_import_source(container="photos"))
    repository.create(stored)

    assert (
        repository.find_by_import_source(media_import_source(container="photos"))
        == stored.media
    )


def test_a_different_container_is_a_different_import_source(
    repository: MongoMediaRepository,
) -> None:
    repository.create(_stored(import_source=media_import_source(container="photos")))

    assert (
        repository.find_by_import_source(media_import_source(container="thumbnails"))
        is None
    )
    assert repository.find_by_import_source(media_import_source(container=None)) is None


def test_media_without_an_import_source_never_matches(
    repository: MongoMediaRepository,
) -> None:
    repository.create(_stored(import_source=None))

    assert repository.find_by_import_source(media_import_source(container=None)) is None


def test_creates_the_indexes_the_queries_need(
    repository: MongoMediaRepository, database: Database
) -> None:
    repository.create_indexes()
    keys = {
        tuple(index["key"])
        for index in database[COLLECTION].index_information().values()
    }

    assert (("associations.fragmentId", 1),) in keys
    assert (("associations.fragmentId", 1), ("type", 1)) in keys
    assert (("representations.original.checksum.value", 1),) in keys
    assert (
        ("importSource.system", 1),
        ("importSource.fileId", 1),
        ("importSource.container", 1),
    ) in keys


def test_replacing_metadata_keeps_the_same_document_id(
    repository: MongoMediaRepository, database: Database
) -> None:
    stored = _stored()
    repository.create(stored)
    repository.replace(
        attr.evolve(stored, media=attr.evolve(stored.media, caption="Reverse"))
    )

    assert database[COLLECTION].count_documents({}) == 1
    document = database[COLLECTION].find_one({})
    assert document is not None
    assert document["_id"] == str(stored.media.id)


def test_unknown_media_id_is_not_a_mongo_error(
    repository: MongoMediaRepository,
) -> None:
    missing = MediaId("00000000-0000-4000-8000-000000000000")

    assert repository.find_by_id(missing) is None
