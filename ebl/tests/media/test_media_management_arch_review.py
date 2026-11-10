"""Independent architecture/recovery regression cases."""

from ebl.tests.media.test_media_management_uploads import MediaTestUser

import uuid

import pytest
from gridfs import GridFS

from ebl.media.application.media_stored import StoredMedia, StoredMediaRepresentations
from ebl.media.domain import Media, MediaId, MediaRepresentations, MediaType
from ebl.media.domain.publication import MediaSubmission, PublicationStatus
from ebl.media.infrastructure.legacy_media_handles import (
    LegacyRepresentationAdoption,
    legacy_import_source,
)
from ebl.tests.media.factories import copy_media, representations, stored_media
from ebl.tests.media.factories import association
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)

from ebl.media.infrastructure.media_recovery import recover_media
from ebl.tests.media.test_media_management_uploads import (
    client,
    upload,
)


def test_failed_commit_retry_recovery_collects_superseded_upload_generation(
    management_runtime, media_database, monkeypatch
):
    repository = management_runtime.management.repository
    commit = repository.commit_upload
    key = str(uuid.uuid4())
    api = client(management_runtime)

    def fail(*args, **kwargs):
        raise RuntimeError("Injected metadata commit failure")

    monkeypatch.setattr(repository, "commit_upload", fail)
    assert upload(api, key=key).status_code == 500
    assert media_database["media.files"].count_documents({}) == 5
    monkeypatch.setattr(repository, "commit_upload", commit)
    saved = upload(api, key=key)
    assert saved.status_code == 201
    item = saved.json["media"][0]
    assert media_database["media.files"].count_documents({}) == 10

    recover_media(media_database, apply=True, quiescent=True)

    assert media_database["media.files"].count_documents({}) == 5
    assert (
        api.simulate_get(item["representations"]["original"]["url"]).status_code == 200
    )
    assert upload(api, key=key).status_code == 200


def test_deleted_upload_does_not_allow_reuse_of_idempotency_identity(
    management_runtime, media_database
):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    key = str(uuid.uuid4())
    item = upload(api, key=key).json["media"][0]
    assert api.simulate_delete(f"/media/{item['id']}?fragment=K.1").status_code == 204
    recover_media(media_database, apply=True, quiescent=True)
    assert upload(api, key=key).status_code == 409
    assert media_database.media.count_documents({}) == 0


def test_retry_then_remove_recovery_also_collects_old_failed_generation(
    management_runtime, media_database, monkeypatch
):
    repository = management_runtime.management.repository
    commit = repository.commit_upload
    key = str(uuid.uuid4())
    api = client(management_runtime, user=MediaTestUser(manager=True))

    def fail(*args, **kwargs):
        raise RuntimeError("Injected metadata commit failure")

    monkeypatch.setattr(repository, "commit_upload", fail)
    assert upload(api, key=key).status_code == 500
    monkeypatch.setattr(repository, "commit_upload", commit)
    item = upload(api, key=key).json["media"][0]
    assert media_database["media.files"].count_documents({}) == 10
    assert api.simulate_delete(f"/media/{item['id']}?fragment=K.1").status_code == 204
    recover_media(media_database, apply=True, quiescent=True)
    assert media_database["media.files"].count_documents({}) == 0
    assert upload(api, key=key).status_code == 409


@pytest.mark.parametrize(
    "reviewer,reviewed_at,attestation",
    [
        (None, None, True),
        ("auth0|manager", None, True),
        (None, "2026-11-09", True),
        ("auth0|manager", "2026-11-09", False),
    ],
)
def test_explicit_publication_requires_review_and_attestation(
    reviewer, reviewed_at, attestation
):
    with pytest.raises(ValueError):
        MediaSubmission(
            uploader_id="auth0|contributor",
            uploaded_at="2026-11-09",
            rights_statement="Permission for eBL",
            permission_attested=attestation,
            publication_status=PublicationStatus.PUBLISHED,
            reviewer_id=reviewer,
            reviewed_at=reviewed_at,
        )


def test_legacy_svg_photo_conversion_returns_structured_validation_error(
    management_runtime,
):
    legacy = copy_media(
        media_representations=representations(original_mime_type="image/svg+xml")
    )
    management_runtime.management.repository.create(stored_media(legacy))
    result = client(
        management_runtime, user=MediaTestUser(manager=True)
    ).simulate_patch(f"/media/{legacy.id}?fragment=K.1", json={"type": "PHOTO"})
    assert result.status_code == 422, result.text
    assert "description" in result.json


def test_http_remove_and_offline_cleanup_preserve_borrowed_legacy_original(
    management_runtime, media_database
):
    original = image_bytes()
    file_id = GridFS(media_database, "photos").put(original)
    identifier = MediaId.create()
    representation = image_representation(original)
    handle = management_runtime.store.adopt_legacy(
        LegacyRepresentationAdoption(identifier, "photos", file_id, representation)
    )
    legacy = Media(
        id=identifier,
        type=MediaType.PHOTO,
        original_filename="legacy.png",
        representations=MediaRepresentations(representation),
        associations=(association(),),
        import_source=legacy_import_source("photos", file_id),
    )
    management_runtime.management.repository.create(
        StoredMedia(legacy, StoredMediaRepresentations(handle))
    )
    api = client(management_runtime, user=MediaTestUser(manager=True))
    assert (
        api.simulate_get(f"/media/{identifier}/file?fragment=K.1").content == original
    )
    assert api.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 204
    recover_media(media_database, apply=True, quiescent=True)
    assert GridFS(media_database, "photos").get(file_id).read() == original
