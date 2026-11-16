import pytest
from ebl.errors import DataError
from ebl.media.application.media_management import validate_metadata
from ebl.media.domain.publication import MediaSubmission, PublicationStatus


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
