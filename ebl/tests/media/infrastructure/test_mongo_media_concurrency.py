from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from pymongo import ReadPreference
from pymongo.database import Database

from ebl.media.application.media_errors import MediaAlreadyExistsError
from ebl.media.domain import MediaId, MediaImportSource
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import association, copy_media, photo_media, stored_media
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_standalone_preflight_does_not_mutate(
    media_database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    def standalone(_self: Database, *_args: object, **_kwargs: object) -> dict:
        return {"isWritablePrimary": True}

    monkeypatch.setattr(Database, "command", standalone)
    with pytest.raises(ValueError, match="replica set"):
        MongoMediaRepository(media_database).create_indexes()
    assert media_database.list_collection_names() == []


def test_transactions_override_secondary_read_preference(
    media_database: Database,
) -> None:
    database = media_database.with_options(read_preference=ReadPreference.SECONDARY)
    repository = MongoMediaRepository(database)
    repository.create_indexes()
    item = stored_media()
    repository.create(item)
    assert repository.find_stored_by_id(item.media.id) == item


def test_concurrent_source_imports_have_one_winner(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    barrier = Barrier(2)
    source = MediaImportSource("gridfs", "ObjectId:source")

    def create(_index: int) -> bool:
        item = stored_media(
            photo_media(media_id_=MediaId.create(), import_source=source)
        )
        barrier.wait(timeout=10)
        try:
            mongo_media_repository.create(item)
        except MediaAlreadyExistsError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(create, range(2))) == [False, True]
    assert len(mongo_media_repository.find_by_fragment(MuseumNumber.of("K.1"))) == 1


def test_concurrent_promotions_have_linearizable_snapshots(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    fragment = MuseumNumber.of("K.1")
    first = stored_media(photo_media(associations=(association(is_primary=False),)))
    second = stored_media(copy_media(associations=(association(is_primary=False),)))
    for item in (first, second):
        mongo_media_repository.create(item)
    barrier = Barrier(2)

    def promote(media_id: MediaId) -> list[MediaId]:
        barrier.wait(timeout=10)
        result = mongo_media_repository.set_primary(fragment, media_id)
        return [item.id for item in result if item.association_for(fragment).is_primary]

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(promote, (first.media.id, second.media.id))) == [
            [first.media.id],
            [second.media.id],
        ]
    assert (
        sum(
            item.association_for(fragment).is_primary
            for item in mongo_media_repository.find_by_fragment(fragment)
        )
        == 1
    )


def test_explicit_primary_create_after_promotion_preserves_requested_state(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    first = stored_media(photo_media())
    second = stored_media(copy_media())
    mongo_media_repository.create(first)
    mongo_media_repository.set_primary(MuseumNumber.of("K.1"), first.media.id)
    mongo_media_repository.create(second)
    assert mongo_media_repository.find_stored_by_id(second.media.id) == second
