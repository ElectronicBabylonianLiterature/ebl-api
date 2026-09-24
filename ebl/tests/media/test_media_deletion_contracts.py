import pytest

from ebl.media.application import MediaAlreadyExistsError, MediaNotFoundError
from ebl.media.domain import Media, MediaAssociation, MediaId, MediaType
from ebl.tests.media.factories import (
    contract_media,
    stored_media,
    stored_media_sequence,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.tests.media.in_memory_media_service import InMemoryMediaService
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
MISSING_ID = MediaId("550e8400-e29b-41d4-a716-4466554400ff")
K1 = MuseumNumber.of("K.1")


def photo() -> Media:
    return contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))


def build_service() -> tuple[
    InMemoryMediaRepository, InMemoryRepresentationStore, InMemoryMediaService
]:
    call_log: list[str] = []
    repository = InMemoryMediaRepository(stored_media_sequence(photo()), call_log)
    store = InMemoryRepresentationStore(call_log)
    return repository, store, InMemoryMediaService(repository, store)


def test_service_deletes_metadata_before_representations() -> None:
    repository, store, service = build_service()

    service.delete_media(PHOTO_ID)

    assert repository.call_log == [
        "repository.delete",
        "store.delete_representation",
        "repository.finish_delete",
    ]
    assert repository.find_by_id(PHOTO_ID) is None
    assert store.deleted_handles == list(
        stored_media_sequence(photo())[0].representations.handles
    )


def test_deleted_media_disappears_from_fragment_reads() -> None:
    repository, _, service = build_service()

    service.delete_media(PHOTO_ID)

    assert repository.find_by_fragment(K1) == ()
    assert repository.find_primary_media(K1) is None
    assert repository.find_in_fragment(PHOTO_ID, K1) is None


def test_service_rejects_deleting_unknown_media() -> None:
    _, store, service = build_service()

    with pytest.raises(MediaNotFoundError):
        service.delete_media(MISSING_ID)

    assert store.deleted_handles == []


def test_representation_deletion_is_retryable_after_a_partial_failure() -> None:
    repository, store, service = build_service()
    stored = repository.find_stored_by_id(PHOTO_ID)
    assert stored is not None
    handle = stored.representations.original
    store.fail_deleting(handle)

    with pytest.raises(RuntimeError, match="delete failed"):
        service.delete_media(PHOTO_ID)

    assert repository.find_by_id(PHOTO_ID) is None

    store.delete_failures.clear()
    service.delete_media(PHOTO_ID)

    assert store.deleted_handles == [handle]
    with pytest.raises(MediaNotFoundError):
        service.delete_media(PHOTO_ID)


def test_metadata_deletion_is_idempotent_for_orphan_recovery() -> None:
    repository, _, _ = build_service()

    first = repository.delete(PHOTO_ID)
    second = repository.delete(PHOTO_ID)

    assert first == second
    assert repository.find_by_id(PHOTO_ID) is None


def test_media_id_cannot_be_reused_until_exact_handle_cleanup_finishes() -> None:
    repository, _, _ = build_service()
    deleted = repository.delete(PHOTO_ID)
    assert deleted is not None

    with pytest.raises(MediaAlreadyExistsError):
        repository.create(stored_media(photo()))

    repository.finish_delete(deleted)

    assert repository.create(stored_media(photo())) == PHOTO_ID


def test_stale_cleanup_cannot_finish_a_newer_deletion_generation() -> None:
    repository, _, _ = build_service()
    old = repository.delete(PHOTO_ID)
    assert old is not None
    repository.finish_delete(old)
    replacement = stored_media(photo(), "replacement")
    repository.create(replacement)
    new = repository.delete(PHOTO_ID)
    assert new == replacement

    repository.finish_delete(old)

    assert repository.delete(PHOTO_ID) == replacement
