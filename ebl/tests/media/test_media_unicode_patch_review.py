"""Independent Unicode patch validation preserves stored state and audit history."""

import json

import pytest

from ebl.tests.media.test_media_management_uploads import (
    MediaTestUser,
    client,
    upload,
)


@pytest.mark.parametrize(
    "metadata",
    [
        {"caption": chr(0xD800)},
        {"rightsStatement": chr(0xDFFF)},
        {"references": [{"id": chr(0xD800)}]},
    ],
)
def test_invalid_unicode_patch_preserves_media_files_and_audit(
    management_runtime, media_database, metadata
):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    identifier = upload(api).json["media"][0]["id"]
    before = media_database.media.find_one({"_id": identifier})
    audit_count = media_database.changelog.count_documents({})
    file_count = media_database["media.files"].count_documents({})

    response = api.simulate_patch(
        f"/media/{identifier}?fragment=K.1",
        body=json.dumps(metadata, ensure_ascii=True),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422, response.text
    assert response.json["description"]
    assert media_database.media.find_one({"_id": identifier}) == before
    assert media_database.changelog.count_documents({}) == audit_count
    assert media_database["media.files"].count_documents({}) == file_count
