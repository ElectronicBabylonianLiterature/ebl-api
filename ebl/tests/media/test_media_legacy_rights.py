import pytest
from gridfs import GridFS

from ebl.media.application.media_stored import StoredMedia, StoredMediaRepresentations
from ebl.media.domain import Media, MediaId, MediaRepresentations, MediaType
from ebl.media.infrastructure.legacy_media_handles import (
    LegacyRepresentationAdoption,
    legacy_import_source,
)
from ebl.tests.media.factories import association
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)
from ebl.tests.media.test_media_management_uploads import client


@pytest.fixture
def legacy_item(management_runtime, media_database):
    original = image_bytes()
    representation = image_representation(original)
    identifier = MediaId.create()
    file_id = GridFS(media_database, "photos").put(original)
    handle = management_runtime.store.adopt_legacy(
        LegacyRepresentationAdoption(identifier, "photos", file_id, representation)
    )
    media = Media(
        id=identifier,
        type=MediaType.PHOTO,
        original_filename="legacy.png",
        representations=MediaRepresentations(representation),
        associations=(association(),),
        import_source=legacy_import_source("photos", file_id),
    )
    management_runtime.management.repository.create(
        StoredMedia(media, StoredMediaRepresentations(handle))
    )
    return identifier, original, file_id


def test_manager_annotations_preserve_legacy_identity_bytes_and_publication(
    management_runtime, media_database, legacy_item
):
    identifier, original, file_id = legacy_item
    api = client(management_runtime, manager=True)
    reader = client(management_runtime, contributor=False)
    before = media_database.media.find_one({"_id": str(identifier)})
    initial = reader.simulate_get("/media?fragment=K.1").json["media"][0]
    assert "rightsAnnotated" not in initial
    assert "publicationStatus" not in initial
    response = api.simulate_patch(
        f"/media/{identifier}?fragment=K.1",
        json={
            "creator": "Verified creator",
            "sourceInstitution": "Museum",
            "rightsStatement": "Reproduction permitted",
            "copyrightHolder": "Museum",
            "description": "Legacy annotation",
            "caption": "Corrected caption",
        },
    )
    assert response.status_code == 200, response.text
    resource = response.json["media"][0]
    assert resource["rightsAnnotated"] is True
    assert resource["rightsStatement"] == "Reproduction permitted"
    for field in (
        "publicationStatus",
        "uploaderId",
        "uploadedAt",
        "reviewerId",
        "permissionAttested",
    ):
        assert field not in resource
    after = media_database.media.find_one({"_id": str(identifier)})
    assert after["importSource"] == before["importSource"]
    assert after["representations"] == before["representations"]
    assert "submission" not in after
    public_resource = reader.simulate_get("/media?fragment=K.1").json["media"][0]
    assert public_resource["rightsAnnotated"] is True
    assert (
        reader.simulate_get(
            public_resource["representations"]["original"]["url"]
        ).content
        == original
    )
    assert GridFS(media_database, "photos").get(file_id).read() == original


def test_legacy_annotations_do_not_fabricate_permission_attestation(
    management_runtime, legacy_item
):
    identifier, _, _ = legacy_item
    manager = client(management_runtime, manager=True)
    assert (
        manager.simulate_patch(
            f"/media/{identifier}?fragment=K.1", json={"permissionAttested": True}
        ).status_code
        == 422
    )
    contributor = client(management_runtime)
    assert (
        contributor.simulate_patch(
            f"/media/{identifier}?fragment=K.1", json={"rightsStatement": "Changed"}
        ).status_code
        == 403
    )
