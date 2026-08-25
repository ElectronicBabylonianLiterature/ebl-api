import attr
import pytest
from pymongo.database import Database

from ebl.media.application import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    StoredMedia,
)
from ebl.media.domain import MediaAssociation, MediaId, MediaType
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import contract_media, stored_media
from ebl.tests.media.in_memory_media import InMemoryMediaRepository
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
MISSING_ID = MediaId("550e8400-e29b-41d4-a716-4466554400ff")
K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")


@pytest.fixture(params=["in-memory", "mongo"])
def repository(request, database: Database) -> MediaRepository:
    if request.param == "in-memory":
        return InMemoryMediaRepository()
    return MongoMediaRepository(database)


def _photo(handle_prefix: str = "photo", is_primary: bool = True) -> StoredMedia:
    return stored_media(
        contract_media(
            PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, is_primary),)
        ),
        handle_prefix,
    )


def _copy(is_primary: bool = False) -> StoredMedia:
    return stored_media(
        contract_media(COPY_ID, MediaType.COPY, (MediaAssociation(K1, 1, is_primary),)),
        "copy",
    )


def test_create_returns_the_media_id(repository: MediaRepository) -> None:
    assert repository.create(_photo()) == PHOTO_ID


def test_create_rejects_an_existing_media_id(repository: MediaRepository) -> None:
    repository.create(_photo())

    with pytest.raises(MediaAlreadyExistsError):
        repository.create(_photo("other"))


def test_replace_returns_the_previous_state(repository: MediaRepository) -> None:
    original = _photo()
    repository.create(original)
    replacement = _photo("replacement")

    assert repository.replace(replacement) == original
    assert repository.find_stored_by_id(PHOTO_ID) == replacement


def test_replace_preserves_media_identity(repository: MediaRepository) -> None:
    repository.create(_photo())
    replacement = _photo("replacement")
    repository.replace(replacement)
    current = repository.find_by_id(PHOTO_ID)

    assert current is not None
    assert current.id == PHOTO_ID


def test_metadata_only_replace_supersedes_no_handles(
    repository: MediaRepository,
) -> None:
    original = _photo()
    repository.create(original)
    replacement = attr.evolve(
        original, media=attr.evolve(original.media, caption="Obverse")
    )
    previous = repository.replace(replacement)

    assert previous.superseded_by(replacement) == ()
    current = repository.find_by_id(PHOTO_ID)
    assert current is not None
    assert current.caption == "Obverse"


def test_replace_reports_superseded_handles(repository: MediaRepository) -> None:
    original = _photo()
    repository.create(original)
    replacement = _photo("replacement")
    previous = repository.replace(replacement)

    assert set(previous.superseded_by(replacement)) == set(
        original.representations.handles
    )


def test_replace_requires_an_existing_media(repository: MediaRepository) -> None:
    with pytest.raises(MediaNotFoundError):
        repository.replace(_photo())


def test_replace_many_returns_previous_states_positionally(
    repository: MediaRepository,
) -> None:
    photo = _photo()
    copy = _copy()
    repository.create(photo)
    repository.create(copy)
    replacements = (_photo("new-photo", False), _copy(True))

    previous = repository.replace_many(replacements)

    assert previous == (photo, copy)
    assert repository.find_primary_media(K1) == replacements[1].media


def test_replace_many_of_nothing_is_a_no_op(repository: MediaRepository) -> None:
    repository.create(_photo())

    assert repository.replace_many(()) == ()
    assert repository.find_stored_by_id(PHOTO_ID) is not None


def test_replace_many_rejects_duplicate_media_ids(
    repository: MediaRepository,
) -> None:
    repository.create(_photo())

    with pytest.raises(ValueError):
        repository.replace_many((_photo("a"), _photo("b")))


def test_replace_many_rejects_a_missing_target_before_mutating(
    repository: MediaRepository,
) -> None:
    photo = _photo()
    repository.create(photo)
    missing = stored_media(
        contract_media(MISSING_ID, MediaType.COPY, (MediaAssociation(SM2, 0, True),)),
        "missing",
    )

    with pytest.raises(MediaNotFoundError):
        repository.replace_many((_photo("replacement"), missing))

    assert repository.find_stored_by_id(PHOTO_ID) == photo


def test_delete_removes_media_metadata(repository: MediaRepository) -> None:
    repository.create(_photo())
    repository.delete(PHOTO_ID)

    assert repository.find_by_id(PHOTO_ID) is None


def test_delete_is_idempotent(repository: MediaRepository) -> None:
    repository.delete(MISSING_ID)
    repository.delete(MISSING_ID)

    assert repository.find_by_id(MISSING_ID) is None
