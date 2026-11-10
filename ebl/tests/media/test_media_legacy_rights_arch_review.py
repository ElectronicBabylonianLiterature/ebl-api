"""Independent review of legacy rights annotations and publication isolation."""

from ebl.tests.media.test_media_management_uploads import MediaTestUser

import attr
import pytest

from ebl.media.domain.publication import MediaRights, MediaSubmission
from ebl.media.infrastructure.media_documents import load_stored, stored_document
from ebl.tests.media.factories import photo_media, stored_media
from ebl.tests.media.test_media_management_uploads import client


@pytest.mark.parametrize(
    "metadata",
    [
        {"caption": "Changed"},
        {"creator": "Changed"},
        {"sourceInstitution": "Changed"},
        {"description": "Changed"},
    ],
)
def test_contributor_cannot_edit_any_legacy_metadata(management_runtime, metadata):
    legacy = photo_media()
    management_runtime.management.repository.create(stored_media(legacy))
    response = client(management_runtime).simulate_patch(
        f"/media/{legacy.id}?fragment=K.1", json=metadata
    )
    assert response.status_code == 403


def test_upload_cannot_be_marked_legacy_through_domain_annotations():
    submission = MediaSubmission(
        uploader_id="auth0|contributor",
        uploaded_at="2026-11-09T12:00:00+00:00",
        rights_statement="Permission for eBL reproduction",
        permission_attested=True,
    )
    with pytest.raises(ValueError, match="cannot coexist"):
        attr.evolve(photo_media(), submission=submission, rights=MediaRights())


@pytest.mark.parametrize(
    "rights",
    [
        {"rights_statement": 42},
        {"permission_attested": True},
        {"publication_status": "PUBLISHED"},
        {"reviewer_id": "auth0|fabricated"},
        None,
    ],
)
def test_malformed_legacy_rights_fail_closed_without_invented_publication(rights):
    document = stored_document(stored_media())
    document["rights"] = rights
    with pytest.raises((TypeError, ValueError)):
        load_stored(document)


def test_annotation_cannot_be_used_to_publish_an_unreviewed_upload(
    management_runtime,
):
    submission = MediaSubmission(
        uploader_id="auth0|contributor",
        uploaded_at="2026-11-09T12:00:00+00:00",
        rights_statement="Permission for eBL reproduction",
        permission_attested=True,
    )
    pending = attr.evolve(photo_media(), submission=submission)
    repository = management_runtime.management.repository
    repository.create(stored_media(pending))
    response = client(
        management_runtime, user=MediaTestUser(manager=True)
    ).simulate_patch(
        f"/media/{pending.id}?fragment=K.1",
        json={"creator": "Annotated creator", "rightsStatement": "Corrected rights"},
    )
    assert response.status_code == 200, response.text
    resource = response.json["media"][0]
    assert resource["publicationStatus"] == "PENDING_REVIEW"
    assert "rightsAnnotated" not in resource
    reader = client(management_runtime, user=MediaTestUser(contributor=False))
    assert reader.simulate_get("/media?fragment=K.1").json == {"media": []}
