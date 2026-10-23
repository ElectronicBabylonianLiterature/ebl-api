import attr
import pytest

from ebl.media.application.media_errors import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
)
from ebl.media.domain import MediaImportSource
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import association, copy_media, photo_media, stored_media
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_unique_source_and_identity(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    source = MediaImportSource("gridfs", "ObjectId:abc", container="photos")
    first = stored_media(photo_media(import_source=source))
    mongo_media_repository.create(first)
    with pytest.raises(MediaAlreadyExistsError):
        mongo_media_repository.create(first)
    with pytest.raises(MediaAlreadyExistsError):
        mongo_media_repository.create(stored_media(copy_media(import_source=source)))
    assert len(mongo_media_repository.find_by_fragment(MuseumNumber.of("K.1"))) == 1


def test_replace_returns_previous_and_retains_handles(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    first = stored_media(photo_media())
    replacement = attr.evolve(first, media=attr.evolve(first.media, caption="updated"))
    mongo_media_repository.create(first)
    previous = mongo_media_repository.replace(replacement)
    assert previous == first
    assert mongo_media_repository.find_stored_by_id(first.media.id) == replacement
    assert not first.superseded_by(replacement)
    with pytest.raises(MediaNotFoundError):
        mongo_media_repository.replace(stored_media(copy_media()))


def test_batch_rolls_back_missing_and_duplicate_sources(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    first = stored_media(photo_media())
    second = stored_media(copy_media())
    mongo_media_repository.create(first)
    changed = attr.evolve(first, media=attr.evolve(first.media, caption="updated"))
    with pytest.raises(MediaNotFoundError):
        mongo_media_repository.replace_many((changed, second))
    assert mongo_media_repository.find_stored_by_id(first.media.id) == first
    with pytest.raises(ValueError):
        mongo_media_repository.replace_many((first, first))
    previous = mongo_media_repository.replace_many(())
    assert previous == ()
    source = MediaImportSource("gridfs", "abc")
    with pytest.raises(MediaAlreadyExistsError):
        mongo_media_repository.replace_many(
            tuple(
                attr.evolve(item, media=attr.evolve(item.media, import_source=source))
                for item in (first, second)
            )
        )


def test_atomic_source_swap(mongo_media_repository: MongoMediaRepository) -> None:
    first = stored_media(photo_media(import_source=MediaImportSource("gridfs", "a")))
    second = stored_media(copy_media(import_source=MediaImportSource("gridfs", "b")))
    for item in (first, second):
        mongo_media_repository.create(item)
    replacements = (
        attr.evolve(
            first,
            media=attr.evolve(first.media, import_source=second.media.import_source),
        ),
        attr.evolve(
            second,
            media=attr.evolve(second.media, import_source=first.media.import_source),
        ),
    )
    previous = mongo_media_repository.replace_many(replacements)
    assert previous == (first, second)
    for item in replacements:
        assert item.media.import_source is not None
        assert (
            mongo_media_repository.find_by_import_source(item.media.import_source)
            == item.media
        )


def test_source_conflict_rolls_back_replace(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    source = MediaImportSource("gridfs", "source")
    first = stored_media(photo_media(import_source=source))
    second = stored_media(copy_media())
    for item in (first, second):
        mongo_media_repository.create(item)
    with pytest.raises(MediaAlreadyExistsError):
        mongo_media_repository.replace(
            attr.evolve(second, media=attr.evolve(second.media, import_source=source))
        )
    assert mongo_media_repository.find_stored_by_id(second.media.id) == second


def test_primary_preserves_other_associations(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    fragment = MuseumNumber.of("K.1")
    first = stored_media(
        photo_media(associations=(association(), association(fragment_id="K.2")))
    )
    second = stored_media(copy_media(associations=(association(is_primary=False),)))
    for item in (first, second):
        mongo_media_repository.create(item)
    selected = mongo_media_repository.set_primary(fragment, second.media.id)
    assert [
        item.id for item in selected if item.association_for(fragment).is_primary
    ] == [second.media.id]
    current_first = mongo_media_repository.find_by_id(first.media.id)
    assert current_first is not None
    assert current_first.association_for("K.2").is_primary
    assert mongo_media_repository.find_primary_photo(fragment) is None
    with pytest.raises(MediaNotFoundError):
        mongo_media_repository.set_primary(MuseumNumber.of("K.3"), second.media.id)


def test_tombstone_reserves_source_and_rejects_stale_generation(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    source = MediaImportSource("gridfs", "source")
    first = stored_media(photo_media(import_source=source))
    mongo_media_repository.create(first)
    deleted = mongo_media_repository.delete(first.media.id)
    assert deleted is not None
    assert deleted.deletion_token
    repeated_deletion = mongo_media_repository.delete(first.media.id)
    assert repeated_deletion == deleted
    assert mongo_media_repository.find_by_id(first.media.id) is None
    with pytest.raises(MediaAlreadyExistsError):
        mongo_media_repository.create(stored_media(copy_media(import_source=source)))
    with pytest.raises(ValueError, match="tombstoned"):
        mongo_media_repository.create(deleted)
    mongo_media_repository.finish_delete(first)
    deletion_after_stale_completion = mongo_media_repository.delete(first.media.id)
    assert deletion_after_stale_completion == deleted
    mongo_media_repository.finish_delete(deleted)
    mongo_media_repository.create(first)
    newer_deletion = mongo_media_repository.delete(first.media.id)
    assert newer_deletion != deleted
    mongo_media_repository.finish_delete(deleted)
    deletion_after_old_completion = mongo_media_repository.delete(first.media.id)
    assert deletion_after_old_completion == newer_deletion
    assert newer_deletion is not None
    mongo_media_repository.finish_delete(newer_deletion)
    deletion_after_completion = mongo_media_repository.delete(first.media.id)
    assert deletion_after_completion is None
    mongo_media_repository.create(stored_media(copy_media(import_source=source)))
