from collections.abc import Callable

import pytest
from pymongo.database import Database
from pymongo.errors import OperationFailure

from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_preflight import (
    complete_filename_index,
    prepare_legacy_indexes,
)
from ebl.media.infrastructure.backfill_sources import LegacyPhotoSources


def test_partial_index_cannot_hide_competing_originals(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    legacy_photo("K.1.jpeg")
    files = database["photos.files"]
    files.drop_indexes()
    files.create_index(
        "filename", name="partial", partialFilterExpression={"filename": "K.1.jpg"}
    )
    before = {
        name: list(database[name].find()) for name in database.list_collection_names()
    }
    indexes = files.index_information()
    with pytest.raises(ValueError, match="complete"):
        tuple(migration_factory(initialize=False).plan_batch(BackfillRequest()))
    assert files.index_information() == indexes
    assert {
        name: list(database[name].find()) for name in database.list_collection_names()
    } == before
    prepare_legacy_indexes(database)
    assert (
        LegacyPhotoSources(database).filename_index() == "media_legacy_photo_filename"
    )
    results = tuple(migration_factory(initialize=False).plan_batch(BackfillRequest()))
    assert {result.reason for result in results} == {"multiple-originals"}
    assert all(result.outcome == "review" for result in results)


@pytest.mark.parametrize(
    "information",
    [
        {},
        {"key": [("uploadDate", 1), ("filename", 1)]},
        {"key": [("filename", "hashed")]},
        {"key": [("filename", 1), ("location", "2dsphere")]},
        {"key": [("filename", 1), ("description", "text")]},
        {"key": [("filename", 1), ("extra.$**", 1)]},
        {"key": [("filename", 1)], "partialFilterExpression": {}},
        {"key": [("filename", 1)], "hidden": True},
        {"key": [("filename", 1)], "sparse": True},
        {"key": [("filename", 1)], "collation": {"locale": "en"}},
    ],
)
def test_incomplete_or_unusable_index_is_rejected(information: dict) -> None:
    assert complete_filename_index({"unsafe": information}) is None


@pytest.mark.parametrize(
    "information",
    [
        {"key": [("filename", 1)]},
        {"key": [("filename", -1), ("uploadDate", 1)]},
        {"key": [("filename", 1)], "collation": {"locale": "simple"}},
    ],
)
def test_complete_btree_index_is_accepted(information: dict) -> None:
    assert complete_filename_index({"safe": information}) == "safe"


def test_index_preparation_overrides_collection_default_collation(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    database.create_collection("photos.files", collation={"locale": "en"})
    legacy_photo()
    prepare_legacy_indexes(database)
    indexes = database["photos.files"].index_information()
    assert "collation" in indexes["filename_1_uploadDate_1"]
    assert "collation" not in indexes["media_legacy_photo_filename"]
    candidates = tuple(
        migration_factory(initialize=False).plan_batch(BackfillRequest())
    )
    assert candidates[0].outcome == "candidate"


def test_preparation_does_not_replace_unsafe_same_name_index(
    database: Database, legacy_photo: Callable
) -> None:
    legacy_photo()
    files = database["photos.files"]
    files.drop_indexes()
    files.create_index("filename", name="media_legacy_photo_filename", sparse=True)
    before = files.index_information()
    with pytest.raises(OperationFailure):
        prepare_legacy_indexes(database)
    assert files.index_information() == before
