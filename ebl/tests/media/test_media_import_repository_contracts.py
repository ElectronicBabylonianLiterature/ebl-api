import pytest

from ebl.media.application import MediaAlreadyExistsError
from ebl.media.domain import MediaId
from ebl.tests.media.factories import media_import_source, photo_media, stored_media
from ebl.tests.media.in_memory_media import InMemoryMediaRepository

FIRST_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
SECOND_ID = MediaId("550e8400-e29b-41d4-a716-446655440002")


def test_repository_finds_media_by_complete_import_identity() -> None:
    source = media_import_source()
    imported = photo_media(media_id_=FIRST_ID, import_source=source)
    repository = InMemoryMediaRepository((stored_media(imported),))

    assert repository.find_by_import_source(source) == imported
    assert (
        repository.find_by_import_source(media_import_source(container="other")) is None
    )


def test_repository_rejects_duplicate_import_identity_atomically() -> None:
    source = media_import_source()
    existing = photo_media(media_id_=FIRST_ID, import_source=source)
    duplicate = photo_media(media_id_=SECOND_ID, import_source=source)
    repository = InMemoryMediaRepository((stored_media(existing),))

    with pytest.raises(MediaAlreadyExistsError):
        repository.create(stored_media(duplicate))

    assert repository.find_by_id(FIRST_ID) == existing
    assert repository.find_by_id(SECOND_ID) is None


def test_repository_rejects_replacing_with_another_medias_import_identity() -> None:
    source = media_import_source()
    existing = photo_media(media_id_=FIRST_ID, import_source=source)
    replacement = photo_media(media_id_=SECOND_ID, import_source=source)
    repository = InMemoryMediaRepository(
        (stored_media(existing), stored_media(photo_media(media_id_=SECOND_ID)))
    )

    with pytest.raises(MediaAlreadyExistsError):
        repository.replace(stored_media(replacement))

    unchanged = repository.find_by_id(SECOND_ID)
    assert unchanged is not None
    assert unchanged.import_source is None
