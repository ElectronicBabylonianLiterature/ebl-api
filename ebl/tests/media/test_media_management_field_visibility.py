"""Management-only fields are exposed only to managers and the item's uploader."""

import uuid

from ebl.tests.media.test_media_management_uploads import (
    METADATA,
    MediaTestUser,
    client,
    png,
    upload,
)

MANAGEMENT_ONLY_FIELDS = (
    "originalFilename",
    "uploaderId",
    "uploadedAt",
    "permissionAttested",
    "projects",
    "reviewerId",
    "reviewedAt",
    "reviewReason",
)
PRIVATE_DESCRIPTION = "Private uploader note"


def _by_id(response):
    assert response.status_code == 200, response.text
    return {item["id"]: item for item in response.json["media"]}


def _upload_owned_and_published(management_runtime):
    owner = client(management_runtime, user=MediaTestUser(actor="auth0|owner"))
    other = client(management_runtime, user=MediaTestUser(actor="auth0|other"))
    manager = client(
        management_runtime,
        user=MediaTestUser(actor="auth0|manager", manager=True, contributor=False),
    )
    metadata = {**METADATA, "description": PRIVATE_DESCRIPTION}
    own = upload(owner, metadata=metadata)
    assert own.status_code == 201, own.text
    foreign = upload(other, metadata=metadata, content=png("blue"))
    assert foreign.status_code == 201, foreign.text
    own_id = own.json["media"][0]["id"]
    foreign_id = foreign.json["media"][0]["id"]
    published = manager.simulate_post(
        f"/media/{foreign_id}/publish?fragment=K.1", json={}
    )
    assert published.status_code == 200, published.text
    return owner, manager, own_id, foreign_id


def test_contributor_management_view_hides_management_fields_of_others(
    management_runtime,
) -> None:
    owner, _, own_id, foreign_id = _upload_owned_and_published(management_runtime)
    items = _by_id(owner.simulate_get("/media?fragment=K.1&view=management"))
    public = _by_id(owner.simulate_get("/media?fragment=K.1"))

    assert set(items) == {own_id, foreign_id}
    foreign = items[foreign_id]
    for field in MANAGEMENT_ONLY_FIELDS:
        assert field not in foreign
    assert foreign.get("description") != PRIVATE_DESCRIPTION
    assert foreign["publicationStatus"] == "PUBLISHED"
    assert foreign == public[foreign_id]

    own = items[own_id]
    assert own["uploaderId"] == "auth0|owner"
    assert own["originalFilename"] == METADATA["originalFilename"]
    assert own["description"] == PRIVATE_DESCRIPTION
    for field in MANAGEMENT_ONLY_FIELDS:
        assert field in own


def test_manager_management_view_includes_all_management_fields(
    management_runtime,
) -> None:
    _, manager, own_id, foreign_id = _upload_owned_and_published(management_runtime)
    items = _by_id(manager.simulate_get("/media?fragment=K.1&view=management"))

    assert items[own_id]["uploaderId"] == "auth0|owner"
    assert items[foreign_id]["uploaderId"] == "auth0|other"
    assert items[foreign_id]["reviewerId"] == "auth0|manager"
    for identifier in (own_id, foreign_id):
        assert items[identifier]["description"] == PRIVATE_DESCRIPTION
        for field in MANAGEMENT_ONLY_FIELDS:
            assert field in items[identifier]


def test_owner_mutation_response_includes_management_fields(
    management_runtime,
) -> None:
    owner, _, own_id, _ = _upload_owned_and_published(management_runtime)
    response = owner.simulate_patch(
        f"/media/{own_id}?fragment=K.1", json={"caption": "Changed"}
    )
    assert response.status_code == 200, response.text
    item = response.json["media"][0]
    assert item["uploaderId"] == "auth0|owner"
    assert item["description"] == PRIVATE_DESCRIPTION


def test_deeply_nested_metadata_header_is_rejected_as_invalid(
    management_runtime,
) -> None:
    response = client(management_runtime).simulate_post(
        "/media",
        params={"fragment": "K.1"},
        body=b"",
        headers={
            "Content-Type": "image/png",
            "Idempotency-Key": str(uuid.uuid4()),
            "X-Media-Metadata": "[" * 16000,
        },
    )
    assert response.status_code == 422, response.text
