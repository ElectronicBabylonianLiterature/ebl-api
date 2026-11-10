"""Independent regression cases from the upload authorization/security review."""

from ebl.tests.media.test_media_management_uploads import MediaTestUser

import uuid
from io import BytesIO
from typing import cast

import attr
import falcon
import pytest
from falcon import testing
from falcon_auth import FalconAuthMiddleware, NoneAuthBackend

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.application.media_management import MediaConflictError, validate_metadata
from ebl.media.domain import MediaAssociation, MediaId
from ebl.media.domain.publication import MediaSubmission, PublicationStatus
from ebl.media.infrastructure.media_recovery import recover_media
from ebl.media.infrastructure.upload_images import prepare_upload
from ebl.media.web.bootstrap import create_media_routes
from ebl.tests.media.test_media_management_uploads import Fragments
from ebl.tests.media.test_media_management_uploads import (
    client,
    if_match,
    upload,
    png,
)
from ebl.users.domain.user import Guest
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize("invalid_type", [[], {}, None, 1, True])
def test_metadata_rejects_non_string_media_types(invalid_type: object) -> None:
    with pytest.raises(DataError):
        validate_metadata({"type": invalid_type})


@pytest.mark.parametrize("name", ["   ", "\t", "\x00", "../original.png"])
def test_upload_rejects_invalid_original_filename(name: str) -> None:
    with pytest.raises(DataError):
        validate_metadata(
            {
                "type": "PHOTO",
                "originalFilename": name,
                "caption": "Tablet obverse",
                "rightsStatement": "Permission from source institution",
                "permissionAttested": True,
            },
            upload=True,
        )


@pytest.mark.parametrize("rights", ["", "   ", "\t"])
def test_metadata_cannot_clear_existing_publication_rights(rights: str) -> None:
    with pytest.raises(DataError):
        validate_metadata({"rightsStatement": rights})


@pytest.mark.parametrize("attestation", [False, 0, 1, "true", None])
def test_permission_attestation_requires_explicit_boolean_true(
    attestation: object,
) -> None:
    with pytest.raises(DataError):
        validate_metadata({"permissionAttested": attestation})


def test_abandoned_upload_reservation_recovers_and_fences_old_lease(
    management_runtime, media_database
) -> None:
    repository = management_runtime.management.repository
    identifier = MediaId.create()
    first_lease, _ = repository.begin_upload("abandoned", "fingerprint", identifier)
    with prepare_upload(BytesIO(png())) as prepared:
        handles = prepared.store(
            management_runtime.store,
            identifier,
            lambda handle: repository.stage_handle("abandoned", first_lease, handle),
        )
    assert recover_media(media_database) == [
        {"action": "recover-incomplete", "requestId": "abandoned"}
    ]
    assert (
        media_database.mediaUploadRequests.find_one({"_id": "abandoned"})["state"]
        == "staging"
    )
    assert media_database["media.files"].count_documents({}) == 5
    recover_media(media_database, apply=True, quiescent=True)
    assert media_database["media.files"].count_documents({}) == 0
    next_lease, existing = repository.begin_upload(
        "abandoned", "fingerprint", identifier
    )
    assert next_lease != first_lease
    assert existing is None
    # An old writer cannot journal into a later retry's generation.
    with pytest.raises(MediaConflictError, match="no longer current"):
        repository.stage_handle("abandoned", first_lease, handles.original)


def test_uncertain_durable_commit_preserves_files_and_idempotent_retry(
    management_runtime, media_database, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = management_runtime.management.repository
    commit = repository.commit_upload

    def uncertain(*args, **kwargs):
        commit(*args, **kwargs)
        raise RuntimeError("Network interrupted after durable commit")

    monkeypatch.setattr(repository, "commit_upload", uncertain)
    api = client(management_runtime)
    key = str(uuid.uuid4())
    assert upload(api, key=key).status_code == 500
    assert media_database.media.count_documents({}) == 1
    assert media_database["media.files"].count_documents({}) == 5
    assert recover_media(media_database, apply=True, quiescent=True) == []
    monkeypatch.setattr(repository, "commit_upload", commit)
    retried = upload(api, key=key)
    assert retried.status_code == 200
    assert retried.json["media"][0]["publicationStatus"] == "PENDING_REVIEW"
    assert (
        api.simulate_get(
            retried.json["media"][0]["representations"]["original"]["url"]
        ).content
        == png()
    )
    assert media_database["media.files"].count_documents({}) == 5


def test_http_tombstone_keeps_an_already_open_gridfs_reader_alive(
    management_runtime,
) -> None:
    api = client(management_runtime, user=MediaTestUser(manager=True))
    item = upload(api).json["media"][0]
    stored = management_runtime.management.repository.find_stored_by_id(
        MediaId(item["id"])
    )
    with management_runtime.store.open_representation(
        stored.representations.original
    ).content as active_reader:
        assert (
            api.simulate_delete(f"/media/{item['id']}?fragment=K.1").status_code == 204
        )
        assert active_reader.read() == png()
    assert (
        api.simulate_get(item["representations"]["original"]["url"]).status_code == 404
    )


def test_upload_preflight_accepts_authenticated_binary_metadata_headers(
    management_runtime,
) -> None:
    app = falcon.App(
        cors_enable=True,
        middleware=[FalconAuthMiddleware(NoneAuthBackend(Guest))],
    )
    create_media_routes(app, cast(FragmentRepository, Fragments()), management_runtime)
    response = testing.TestClient(app).simulate_options(
        "/media?fragment=K.1",
        headers={
            "Origin": "https://www.ebl.lmu.de",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "authorization, content-type, idempotency-key, x-media-metadata"
            ),
        },
    )
    assert response.status_code == 200
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    allowed = response.headers["Access-Control-Allow-Headers"].lower()
    for header in (
        "authorization",
        "content-type",
        "idempotency-key",
        "x-media-metadata",
    ):
        assert header in allowed


def test_mutation_requires_access_to_every_associated_fragment(
    management_runtime,
) -> None:
    restricted_manager = client(management_runtime, user=MediaTestUser(manager=True))
    contributor = client(management_runtime)
    item = upload(contributor).json["media"][0]
    identifier = MediaId(item["id"])
    repository = management_runtime.management.repository
    stored = repository.find_stored_by_id(identifier)
    repository.replace(
        attr.evolve(
            stored,
            media=attr.evolve(
                stored.media,
                associations=stored.media.associations
                + (MediaAssociation(MuseumNumber.of("K.2"), 1),),
            ),
        )
    )
    path = f"/media/{identifier}?fragment=K.1"
    assert (
        contributor.simulate_patch(path, json={"caption": "Changed"}).status_code == 403
    )
    assert (
        restricted_manager.simulate_patch(path, json={"caption": "Changed"}).status_code
        == 403
    )
    assert restricted_manager.simulate_delete(path).status_code == 403
    for action in ("publish", "reject", "primary"):
        assert (
            restricted_manager.simulate_post(
                f"/media/{identifier}/{action}?fragment=K.1", json={}
            ).status_code
            == 403
        )
    authorized_manager = client(
        management_runtime, user=MediaTestUser(manager=True, fragment_access=True)
    )
    assert (
        authorized_manager.simulate_post(
            f"/media/{identifier}/publish?fragment=K.1",
            json={},
            headers=if_match(repository.find_stored_by_id(identifier).media.revision),
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "status", [PublicationStatus.PUBLISHED, PublicationStatus.REJECTED]
)
def test_explicit_reviewed_state_requires_reviewer_identity_and_timestamp(
    status,
) -> None:
    with pytest.raises(ValueError, match="reviewer identity"):
        MediaSubmission(
            uploader_id="auth0|owner",
            uploaded_at="2026-11-09T00:00:00+00:00",
            rights_statement="Permission granted",
            permission_attested=True,
            publication_status=status,
        )


def test_explicit_published_state_requires_permission_attestation() -> None:
    with pytest.raises(ValueError, match="permission attestation"):
        MediaSubmission(
            uploader_id="auth0|owner",
            uploaded_at="2026-11-09T00:00:00+00:00",
            rights_statement="Permission granted",
            permission_attested=False,
            publication_status=PublicationStatus.PUBLISHED,
            reviewer_id="auth0|manager",
            reviewed_at="2026-11-09T00:00:00+00:00",
        )
