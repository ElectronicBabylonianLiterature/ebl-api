from unittest.mock import Mock

import pytest

from ebl.media.infrastructure.upload_images import UploadBusyError
from ebl.media.web.media_response import media_response
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema
from ebl.tests.media.factories import photo_media
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.media.test_media_management_uploads import client


def test_unknown_management_view_is_rejected(management_runtime) -> None:
    response = client(management_runtime).simulate_get("/media?fragment=K.1&view=other")
    assert response.status_code == 422


def test_suppressed_legacy_fallback_is_explicit_in_gallery(
    management_runtime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        management_runtime.service, "legacy_fallback_allowed", lambda number: False
    )
    response = client(management_runtime).simulate_get("/media?fragment=K.1")
    assert response.status_code == 200
    assert response.json["media"] == []
    assert response.json["legacyFallbackAllowed"] is False


def test_oversized_metadata_header_is_rejected_before_upload(
    management_runtime,
) -> None:
    response = client(management_runtime).simulate_post(
        "/media?fragment=K.1",
        body=b"png",
        headers={"X-Media-Metadata": "x" * 16385},
    )
    assert response.status_code == 413


def test_busy_decoder_is_retryable_without_storing_media(
    management_runtime,
    media_database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload = Mock(side_effect=UploadBusyError("Decoder busy"))
    monkeypatch.setattr(management_runtime.management, "upload", upload)
    response = client(management_runtime).simulate_post(
        "/media?fragment=K.1",
        body=b"png",
        headers={"X-Media-Metadata": "{}", "Idempotency-Key": "upload-key"},
    )
    assert response.status_code == 503
    assert response.headers["retry-after"] == "10"
    assert media_database.media.count_documents({}) == 0
    upload.assert_called_once()


def test_unknown_binary_mutation_is_not_found(management_runtime) -> None:
    response = client(management_runtime).simulate_post(
        "/media/550e8400-e29b-41d4-a716-446655440000/other?fragment=K.1",
        json={},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("response_count", [0, 2])
def test_response_serialization_preserves_item_count_guard(
    monkeypatch: pytest.MonkeyPatch,
    response_count: int,
) -> None:
    monkeypatch.setattr(
        FragmentMediaResponseDtoSchema,
        "dump",
        lambda *args: {"media": [{}] * response_count},
    )
    with pytest.raises(ValueError, match="item count"):
        media_response(MuseumNumber.of("K.1"), (photo_media(),))
