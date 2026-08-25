from typing import Tuple

import pytest
from bson import ObjectId
from pymongo.database import Database

from ebl.media.application import (
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationStore,
    StoredRepresentationHandle,
)
from ebl.media.application.fragment_media_service import FragmentMediaService
from ebl.media.domain import Media, MediaId, MediaType
from ebl.media.infrastructure.grid_fs_media_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import (
    association,
    copy_media,
    photo_media,
    stored_media,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.tests.media.route_fixtures import seed_media
from ebl.transliteration.domain.museum_number import MuseumNumber

K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")
MISSING_ID = MediaId("550e8400-e29b-41d4-a716-4466554400ff")

ServiceParts = Tuple[MediaRepository, MediaRepresentationStore, FragmentMediaService]
MongoParts = Tuple[
    MongoMediaRepository, GridFsMediaRepresentationStore, FragmentMediaService
]


@pytest.fixture
def mongo_parts(database: Database) -> MongoParts:
    repository = MongoMediaRepository(database)
    store = GridFsMediaRepresentationStore(database)
    return repository, store, FragmentMediaService(repository, store)


@pytest.fixture(params=["in-memory", "mongo"])
def parts(request, database: Database) -> ServiceParts:
    if request.param == "in-memory":
        repository: MediaRepository = InMemoryMediaRepository()
        store: MediaRepresentationStore = InMemoryRepresentationStore()
    else:
        repository = MongoMediaRepository(database)
        store = GridFsMediaRepresentationStore(database)
    return repository, store, FragmentMediaService(repository, store)


def _create(repository: MediaRepository, *media: Media) -> None:
    for item in media:
        repository.create(stored_media(item, f"stored-{item.id}"))


def _object_id(handle: StoredRepresentationHandle) -> ObjectId:
    return ObjectId(handle.value)


def test_lists_fragment_media_in_canonical_order(parts: ServiceParts) -> None:
    repository, _, service = parts
    photo = photo_media(
        associations=(association(fragment_id=K1, sort_order=1, is_primary=False),)
    )
    copy = copy_media(
        associations=(association(fragment_id=K1, sort_order=0, is_primary=True),)
    )
    _create(repository, photo, copy)

    assert service.list_fragment_media(K1) == (copy, photo)


def test_batch_read_keys_every_fragment(parts: ServiceParts) -> None:
    repository, _, service = parts
    photo = photo_media(associations=(association(fragment_id=K1),))
    _create(repository, photo)

    result = service.find_media_by_fragments((K1, SM2))

    assert result[K1] == (photo,)
    assert result[SM2] == ()


def test_gets_media_within_its_fragment(parts: ServiceParts) -> None:
    repository, _, service = parts
    photo = photo_media(associations=(association(fragment_id=K1),))
    _create(repository, photo)

    assert service.get_fragment_media(K1, photo.id) == photo
    assert service.get_stored_fragment_media(K1, photo.id) is not None


def test_refuses_media_of_another_fragment(parts: ServiceParts) -> None:
    repository, _, service = parts
    photo = photo_media(associations=(association(fragment_id=K1),))
    _create(repository, photo)

    assert service.get_fragment_media(SM2, photo.id) is None
    assert service.get_stored_fragment_media(SM2, photo.id) is None


def test_promotes_one_primary_and_demotes_the_others(parts: ServiceParts) -> None:
    repository, _, service = parts
    photo = photo_media(
        associations=(association(fragment_id=K1, sort_order=0, is_primary=True),)
    )
    copy = copy_media(
        associations=(association(fragment_id=K1, sort_order=1, is_primary=False),)
    )
    _create(repository, photo, copy)

    result = service.set_primary_media(K1, copy.id)
    primary = [item.id for item in result if item.association_for(K1).is_primary]

    assert primary == [copy.id]


def test_primary_promotion_rejects_media_of_another_fragment(
    parts: ServiceParts,
) -> None:
    repository, _, service = parts
    photo = photo_media(associations=(association(fragment_id=K1),))
    _create(repository, photo)

    with pytest.raises(MediaNotFoundError):
        service.set_primary_media(SM2, photo.id)


def test_primary_promotion_rejects_unknown_media(parts: ServiceParts) -> None:
    _, _, service = parts

    with pytest.raises(MediaNotFoundError):
        service.set_primary_media(K1, MISSING_ID)


def test_delete_rejects_unknown_media(parts: ServiceParts) -> None:
    _, _, service = parts

    with pytest.raises(MediaNotFoundError):
        service.delete_media(MISSING_ID)


def test_deletes_metadata_before_binaries(
    mongo_parts: MongoParts, database: Database
) -> None:
    repository, store, service = mongo_parts
    media = photo_media(associations=(association(fragment_id=K1),))
    stored = seed_media(repository, store, media)
    service.delete_media(media.id)

    assert repository.find_by_id(media.id) is None
    for handle in stored.representations.handles:
        assert (
            database["mediaRepresentations.files"].find_one({"_id": _object_id(handle)})
            is None
        )


def test_primary_promotion_keeps_stored_handles(mongo_parts: MongoParts) -> None:
    repository, store, service = mongo_parts
    media = photo_media(associations=(association(fragment_id=K1, is_primary=False),))
    stored = seed_media(repository, store, media)
    service.set_primary_media(K1, media.id)
    current = service.get_stored_fragment_media(K1, media.id)

    assert current is not None
    assert current.representations == stored.representations


def test_primary_promotion_keeps_other_fragment_associations(
    mongo_parts: MongoParts,
) -> None:
    repository, store, service = mongo_parts
    media = photo_media(
        associations=(
            association(fragment_id=K1, sort_order=0, is_primary=False),
            association(fragment_id=SM2, sort_order=0, is_primary=True),
        )
    )
    seed_media(repository, store, media)
    service.set_primary_media(K1, media.id)
    current = service.get_fragment_media(SM2, media.id)

    assert current is not None
    assert current.association_for(SM2).is_primary is True
    assert current.type is MediaType.PHOTO
