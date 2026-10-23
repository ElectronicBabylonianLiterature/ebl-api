import attr
import pytest
from pymongo.database import Database

from ebl.common.domain.project import ResearchProject
from ebl.media.domain import MediaId, MediaImportSource
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.tests.media.factories import (
    association,
    copy_media,
    media_reference,
    photo_media,
    representations,
    stored_media,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_roundtrip_complete_state(mongo_media_repository: MongoMediaRepository) -> None:
    source = MediaImportSource("gridfs", "ObjectId:abc", container="photos")
    item = stored_media(
        photo_media(
            media_representations=representations(display_mime_type="image/png"),
            projects=(ResearchProject.CAIC,),
            references=(media_reference(),),
            caption="caption",
            attribution="Museum",
            import_source=source,
        )
    )
    assert mongo_media_repository.create(item) == item.media.id
    assert mongo_media_repository.find_stored_by_id(item.media.id) == item
    assert mongo_media_repository.find_by_id(item.media.id) == item.media
    assert mongo_media_repository.find_by_import_source(source) == item.media
    assert (
        mongo_media_repository.find_by_import_source(MediaImportSource("other", "abc"))
        is None
    )


def test_scoped_batch_reads_preserve_order_and_empty_keys(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    first_fragment, second_fragment, missing = (
        MuseumNumber.of(value) for value in ("K.1", "K.2", "K.3")
    )
    first = stored_media(
        photo_media(
            associations=(
                association(sort_order=2),
                association(fragment_id=second_fragment),
            )
        )
    )
    second = stored_media(copy_media(associations=(association(sort_order=1),)))
    for item in (first, second):
        mongo_media_repository.create(item)
    assert mongo_media_repository.find_by_fragments(
        (first_fragment, missing, first_fragment)
    ) == {
        first_fragment: (second.media, first.media),
        missing: (),
    }
    assert mongo_media_repository.find_by_fragments(()) == {}
    assert (
        mongo_media_repository.find_in_fragment(first.media.id, first_fragment)
        == first.media
    )
    assert mongo_media_repository.find_in_fragment(first.media.id, missing) is None
    assert (
        mongo_media_repository.find_stored_in_fragment(second.media.id, second_fragment)
        is None
    )
    assert mongo_media_repository.find_primary_media(first_fragment) == first.media
    assert mongo_media_repository.find_primary_photo(first_fragment) == first.media
    assert mongo_media_repository.find_by_id(MediaId.create()) is None


def test_initialization_and_source_consistency(media_database: Database) -> None:
    repository = MongoMediaRepository(media_database)
    assert media_database.list_collection_names() == []
    with pytest.raises(ValueError, match="initialized"):
        repository.create(stored_media())
    repository.create_indexes()
    repository.create_indexes()
    assert "media_import_source" in media_database.media.index_information()
    assert media_database.mediaSources.index_information()["_id_"]["key"] == [
        ("_id", 1)
    ]
    media_database.mediaSources.insert_one({"_id": "orphan", "mediaId": "orphan"})
    with pytest.raises(ValueError, match="reconciliation"):
        repository.create_indexes()


def test_duplicate_preexisting_sources_prevent_index_setup(
    media_database: Database,
) -> None:
    media_database.media.insert_many(
        [
            {"_id": "one", "sourceKey": "same"},
            {"_id": "two", "sourceKey": "same"},
        ]
    )
    with pytest.raises(ValueError, match="duplicate"):
        MongoMediaRepository(media_database).create_indexes()


def test_read_without_display_or_thumbnails(
    mongo_media_repository: MongoMediaRepository,
) -> None:
    item = stored_media(
        photo_media(media_representations=representations(thumbnails=()))
    )
    mongo_media_repository.create(item)
    assert mongo_media_repository.find_stored_by_id(item.media.id) == item
    changed = attr.evolve(item, media=attr.evolve(item.media, caption="changed"))
    assert mongo_media_repository.replace(changed) == item
