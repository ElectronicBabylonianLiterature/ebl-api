"""Malformed Unicode is rejected before binaries, reservations, or reviews persist."""

import pytest
import json

from ebl.tests.media.test_media_management_uploads import (
    METADATA,
    MediaTestUser,
    client,
    if_match,
    upload,
)


@pytest.mark.parametrize("surrogate", [chr(0xD800), chr(0xDFFF)])
@pytest.mark.parametrize(
    "field",
    [
        "caption",
        "attribution",
        "creator",
        "sourceInstitution",
        "copyrightHolder",
        "rightsStatement",
        "description",
        "originalFilename",
        "reference",
    ],
)
def test_invalid_unicode_upload_never_stages_files(
    management_runtime, media_database, field, surrogate
):
    metadata = {**METADATA, field: surrogate}
    if field == "reference":
        metadata.pop("reference")
        metadata["references"] = [{"id": surrogate}]
    response = upload(client(management_runtime), metadata=metadata)
    assert response.status_code == 422, response.text
    assert response.json["description"]
    assert media_database.media.count_documents({}) == 0
    assert media_database.mediaFiles.count_documents({}) == 0
    assert media_database["media.files"].count_documents({}) == 0
    assert media_database.mediaUploadRequests.count_documents({}) == 0


@pytest.mark.parametrize("operation", ["publish", "reject"])
@pytest.mark.parametrize("surrogate", [chr(0xD800), chr(0xDFFF)])
def test_invalid_unicode_review_never_changes_submission(
    management_runtime, media_database, operation, surrogate
):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    identifier = upload(api).json["media"][0]["id"]
    before = media_database.media.find_one({"_id": identifier})
    response = api.simulate_post(
        f"/media/{identifier}/{operation}?fragment=K.1",
        body=json.dumps({"reason": surrogate}, ensure_ascii=True),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert media_database.media.find_one({"_id": identifier}) == before


@pytest.mark.parametrize(
    "metadata",
    [
        {"caption": chr(0xD800)},
        {"creator": chr(0xDFFF)},
        {"references": [{"id": chr(0xD800)}]},
    ],
)
def test_invalid_unicode_edit_never_changes_metadata(
    management_runtime, media_database, metadata
):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    identifier = upload(api).json["media"][0]["id"]
    before = media_database.media.find_one({"_id": identifier})
    response = api.simulate_patch(
        f"/media/{identifier}?fragment=K.1",
        body=json.dumps(metadata, ensure_ascii=True),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert media_database.media.find_one({"_id": identifier}) == before


def test_valid_non_bmp_unicode_survives_upload_edit_and_review(management_runtime):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    text = "Tablet \U0001f4f7"
    response = upload(
        api, metadata={**METADATA, "caption": text, "references": [{"id": text}]}
    )
    assert response.status_code == 201, response.text
    identifier = response.json["media"][0]["id"]
    assert response.json["media"][0]["caption"] == text
    edited = api.simulate_patch(
        f"/media/{identifier}?fragment=K.1", json={"caption": text + " edited"}
    )
    assert edited.status_code == 200
    published = api.simulate_post(
        f"/media/{identifier}/publish?fragment=K.1",
        json={"reason": text},
        headers=if_match(edited.json["media"][0]["revision"]),
    )
    assert published.status_code == 200
    assert published.json["media"][0]["reviewReason"] == text
