from ebl.media.infrastructure.legacy_media_handles import LegacyRepresentationAdoption
from bson import ObjectId
from typing import Union, cast
from gridfs import GridFS
from pymongo.database import Database
import pytest
from ebl.media.application.media_errors import StoredRepresentationMissingError
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.legacy_media_handles import (
    legacy_handle,
    legacy_import_source,
)
from ebl.tests.media.factories import media_id
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)


@pytest.mark.parametrize("container", ["photos", "thumbnails"])
def test_adoption_is_repeatable_and_deletion_preserves_legacy(
    representation_store: GridFsMediaRepresentationStore,
    media_database: Database,
    container: str,
) -> None:
    file_id = GridFS(media_database, container).put(image_bytes())
    expected = legacy_handle(
        LegacyRepresentationAdoption(
            media_id(), container, file_id, image_representation()
        )
    )
    assert (
        representation_store.adopt_legacy(
            LegacyRepresentationAdoption(
                media_id(), container, file_id, image_representation()
            )
        )
        == expected
    )
    assert (
        representation_store.adopt_legacy(
            LegacyRepresentationAdoption(
                media_id(), container, file_id, image_representation()
            )
        )
        == expected
    )
    with representation_store.open_representation(expected).content as opened:
        assert opened.read() == image_bytes()
    representation_store.delete_representation(expected)
    representation_store.delete_representation(expected)
    assert GridFS(media_database, container).get(file_id).read() == image_bytes()
    with pytest.raises(ValueError, match="revived"):
        representation_store.adopt_legacy(
            LegacyRepresentationAdoption(
                media_id(), container, file_id, image_representation()
            )
        )


def test_typed_identity_distinguishes_object_id_from_string(
    representation_store: GridFsMediaRepresentationStore, media_database: Database
) -> None:
    object_id = ObjectId()
    bucket = GridFS(media_database, "photos")
    bucket.put(image_bytes(), _id=object_id)
    bucket.put(image_bytes(), _id=str(object_id))
    handles = tuple(
        (
            representation_store.adopt_legacy(
                LegacyRepresentationAdoption(
                    media_id(), "photos", value, image_representation()
                )
            )
            for value in (object_id, str(object_id))
        )
    )
    assert handles[0] != handles[1]
    assert legacy_import_source("photos", object_id) != legacy_import_source(
        "photos", str(object_id)
    )


@pytest.mark.parametrize(
    "container, file_id", [("fs", "id"), ("photos", ""), ("photos", 1)]
)
def test_invalid_legacy_identity(container: str, file_id: object) -> None:
    with pytest.raises(ValueError):
        legacy_import_source(container, cast(Union[ObjectId, str], file_id))


def test_missing_legacy_file(
    representation_store: GridFsMediaRepresentationStore,
) -> None:
    with pytest.raises(StoredRepresentationMissingError):
        representation_store.adopt_legacy(
            LegacyRepresentationAdoption(
                media_id(), "photos", ObjectId(), image_representation()
            )
        )


def test_adoption_does_not_create_owned_files(
    representation_store: GridFsMediaRepresentationStore, media_database: Database
) -> None:
    file_id = GridFS(media_database, "photos").put(image_bytes())
    representation_store.adopt_legacy(
        LegacyRepresentationAdoption(
            media_id(), "photos", file_id, image_representation()
        )
    )
    assert media_database["media.files"].count_documents({}) == 0
    assert media_database["media.chunks"].count_documents({}) == 0
