from io import BytesIO

import attr
import pytest

from ebl.media.application import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    RepresentationHandle,
)
from ebl.media.domain import MediaAssociation, MediaId, MediaType
from ebl.tests.media.factories import (
    contract_media,
    original_representation,
    stored_media,
    stored_media_sequence,
)
from ebl.tests.media.in_memory_media import InMemoryMediaRepository
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
MISSING_ID = MediaId("550e8400-e29b-41d4-a716-4466554400ff")
K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")


def test_repository_contract_reads_media_by_fragment_in_fragment_order() -> None:
    photo = contract_media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(K1, 1, False), MediaAssociation(SM2, 0, True)),
    )
    copy = contract_media(COPY_ID, MediaType.COPY, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository(stored_media_sequence(photo, copy))

    assert repository.find_by_fragment(K1) == (copy, photo)
    assert repository.find_by_fragment(SM2) == (photo,)


def test_repository_contract_returns_empty_sequence_for_unknown_fragment() -> None:
    repository = InMemoryMediaRepository()

    assert repository.find_by_fragment(K1) == ()


def test_repository_contract_batch_keys_every_requested_fragment() -> None:
    photo = contract_media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(K1, 0, True), MediaAssociation(SM2, 0, True)),
    )
    repository = InMemoryMediaRepository(stored_media_sequence(photo))
    missing = MuseumNumber.of("BM.99")

    assert repository.find_by_fragments((K1, SM2, missing)) == {
        K1: (photo,),
        SM2: (photo,),
        missing: (),
    }


def test_repository_contract_batch_collapses_duplicate_fragment_ids() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository(stored_media_sequence(photo))

    assert repository.find_by_fragments((K1, K1)) == {K1: (photo,)}


def test_repository_contract_reads_one_media_item_in_fragment_context() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository(stored_media_sequence(photo))

    assert repository.find_in_fragment(PHOTO_ID, K1) == photo
    assert repository.find_in_fragment(PHOTO_ID, SM2) is None
    assert repository.find_in_fragment(MISSING_ID, K1) is None


def test_repository_contract_creates_new_media() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository()

    assert repository.create(stored_media(photo)) == PHOTO_ID
    assert repository.find_by_id(PHOTO_ID) == photo


def test_repository_contract_rejects_creating_an_existing_media_id() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository(stored_media_sequence(photo))

    with pytest.raises(MediaAlreadyExistsError):
        repository.create(stored_media(attr.evolve(photo, caption="Duplicate")))


def test_repository_contract_replaces_metadata_without_changing_identity() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    replacement = attr.evolve(photo, caption="Replacement audit note")
    repository = InMemoryMediaRepository(stored_media_sequence(photo))

    previous = repository.replace(stored_media(replacement, "replacement"))

    assert previous.media == photo
    assert repository.find_by_id(PHOTO_ID) == replacement


def test_repository_contract_rejects_replacing_unknown_media() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository()

    with pytest.raises(MediaNotFoundError):
        repository.replace(stored_media(photo))


def test_repository_contract_deletes_metadata_idempotently() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))
    repository = InMemoryMediaRepository(stored_media_sequence(photo))

    repository.delete(PHOTO_ID)
    repository.delete(PHOTO_ID)

    assert repository.find_by_id(PHOTO_ID) is None
    assert repository.find_by_fragment(K1) == ()


def test_media_errors_identify_the_media_they_describe() -> None:
    not_found = MediaNotFoundError(PHOTO_ID)
    already_exists = MediaAlreadyExistsError(PHOTO_ID)

    assert not_found.media_id == PHOTO_ID
    assert str(not_found) == f"Media {PHOTO_ID} not found."
    assert already_exists.media_id == PHOTO_ID
    assert str(already_exists) == f"Media {PHOTO_ID} already exists."


def test_repository_contract_does_not_expose_representation_reads() -> None:
    assert not hasattr(MediaRepository, "read_original")
    assert not hasattr(MediaRepository, "find_display")


def test_representation_handle_contract_includes_readable_content() -> None:
    handle = RepresentationHandle(
        media_id=PHOTO_ID,
        representation=original_representation(),
        content=BytesIO(b"media-bytes"),
        content_type="image/jpeg",
        length=len(b"media-bytes"),
    )

    assert handle.content.read() == b"media-bytes"
