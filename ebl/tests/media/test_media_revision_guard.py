"""Reviews apply only to the media revision the manager actually reviewed."""

from typing import cast

import falcon
import pytest
from falcon import testing
from falcon_auth import FalconAuthMiddleware, NoneAuthBackend

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.web.bootstrap import create_media_routes
from ebl.tests.media.factories import photo_media, stored_media
from ebl.tests.media.test_media_management_uploads import (
    Fragments,
    MediaTestUser,
    client,
    if_match,
    upload,
)
from ebl.users.domain.user import Guest

STALE_MESSAGE = "Media changed since it was loaded; reload and review again."


def _manager(runtime):
    return client(
        runtime,
        user=MediaTestUser(actor="auth0|manager", manager=True, contributor=False),
    )


def _listed(api, identifier):
    response = api.simulate_get("/media?fragment=K.1&view=management")
    assert response.status_code == 200, response.text
    return next(item for item in response.json["media"] if item["id"] == identifier)


def _pending_upload(runtime):
    owner = client(runtime, user=MediaTestUser(actor="auth0|owner"))
    response = upload(owner)
    assert response.status_code == 201, response.text
    item = response.json["media"][0]
    assert item["revision"] == 0
    return owner, _manager(runtime), item["id"]


def test_new_upload_starts_at_revision_zero_in_management_listing(
    management_runtime, media_database
):
    owner, manager, identifier = _pending_upload(management_runtime)
    assert _listed(owner, identifier)["revision"] == 0
    assert _listed(manager, identifier)["revision"] == 0
    assert media_database.media.find_one({"_id": identifier})["revision"] == 0


def test_revision_is_absent_from_the_public_view(management_runtime):
    owner, manager, identifier = _pending_upload(management_runtime)
    published = manager.simulate_post(
        f"/media/{identifier}/publish?fragment=K.1", json={}, headers=if_match(0)
    )
    assert published.status_code == 200, published.text
    public = owner.simulate_get("/media?fragment=K.1").json["media"]
    assert [item["id"] for item in public] == [identifier]
    assert "revision" not in public[0]


def test_patch_increments_revision_and_sets_etag(management_runtime):
    owner, _, identifier = _pending_upload(management_runtime)
    response = owner.simulate_patch(
        f"/media/{identifier}?fragment=K.1", json={"caption": "Edited"}
    )
    assert response.status_code == 200, response.text
    assert response.json["media"][0]["revision"] == 1
    assert response.headers["ETag"] == '"1"'
    assert _listed(owner, identifier)["revision"] == 1


def test_publish_of_a_changed_item_is_refused_and_leaves_it_pending(
    management_runtime, media_database
):
    owner, manager, identifier = _pending_upload(management_runtime)
    reviewed = _listed(manager, identifier)["revision"]
    edited = owner.simulate_patch(
        f"/media/{identifier}?fragment=K.1", json={"caption": "Unreviewed text"}
    )
    assert edited.status_code == 200, edited.text
    before = media_database.media.find_one({"_id": identifier})

    response = manager.simulate_post(
        f"/media/{identifier}/publish?fragment=K.1",
        json={},
        headers=if_match(reviewed),
    )

    assert response.status_code == 412, response.text
    assert response.json["description"] == STALE_MESSAGE
    assert media_database.media.find_one({"_id": identifier}) == before
    item = _listed(manager, identifier)
    assert item["publicationStatus"] == "PENDING_REVIEW"
    assert item["reviewerId"] is None
    assert item["revision"] == 1


@pytest.mark.parametrize("operation", ["publish", "reject"])
def test_review_without_if_match_is_precondition_required(
    management_runtime, media_database, operation
):
    _, manager, identifier = _pending_upload(management_runtime)
    before = media_database.media.find_one({"_id": identifier})
    response = manager.simulate_post(
        f"/media/{identifier}/{operation}?fragment=K.1", json={}
    )
    assert response.status_code == 428, response.text
    assert media_database.media.find_one({"_id": identifier}) == before


@pytest.mark.parametrize(
    "operation,status", [("publish", "PUBLISHED"), ("reject", "REJECTED")]
)
@pytest.mark.parametrize("header", ['"0"', "0"])
def test_review_with_current_revision_succeeds_and_increments(
    management_runtime, operation, status, header
):
    _, manager, identifier = _pending_upload(management_runtime)
    response = manager.simulate_post(
        f"/media/{identifier}/{operation}?fragment=K.1",
        json={},
        headers={"If-Match": header},
    )
    assert response.status_code == 200, response.text
    item = response.json["media"][0]
    assert item["publicationStatus"] == status
    assert item["reviewerId"] == "auth0|manager"
    assert item["revision"] == 1
    assert response.headers["ETag"] == '"1"'


def test_stale_reject_is_refused(management_runtime):
    owner, manager, identifier = _pending_upload(management_runtime)
    assert (
        owner.simulate_patch(
            f"/media/{identifier}?fragment=K.1", json={"caption": "Edited"}
        ).status_code
        == 200
    )
    response = manager.simulate_post(
        f"/media/{identifier}/reject?fragment=K.1", json={}, headers=if_match(0)
    )
    assert response.status_code == 412, response.text
    assert _listed(manager, identifier)["publicationStatus"] == "PENDING_REVIEW"


@pytest.mark.parametrize("header", ["*", 'W/"0"', '"abc"', '"-1"', '"0", "1"'])
def test_malformed_if_match_is_rejected(management_runtime, header):
    _, manager, identifier = _pending_upload(management_runtime)
    response = manager.simulate_post(
        f"/media/{identifier}/publish?fragment=K.1",
        json={},
        headers={"If-Match": header},
    )
    assert response.status_code == 422, response.text


def test_patch_without_if_match_still_works(management_runtime):
    owner, _, identifier = _pending_upload(management_runtime)
    for revision, caption in enumerate(("First", "Second"), start=1):
        response = owner.simulate_patch(
            f"/media/{identifier}?fragment=K.1", json={"caption": caption}
        )
        assert response.status_code == 200, response.text
        assert response.json["media"][0]["revision"] == revision


def test_patch_with_stale_if_match_is_refused(management_runtime, media_database):
    owner, _, identifier = _pending_upload(management_runtime)
    path = f"/media/{identifier}?fragment=K.1"
    assert (
        owner.simulate_patch(
            path, json={"caption": "First"}, headers=if_match(0)
        ).status_code
        == 200
    )
    before = media_database.media.find_one({"_id": identifier})
    response = owner.simulate_patch(
        path, json={"caption": "Second"}, headers=if_match(0)
    )
    assert response.status_code == 412, response.text
    assert media_database.media.find_one({"_id": identifier}) == before


def test_permission_errors_precede_revision_checks(management_runtime):
    owner, _, identifier = _pending_upload(management_runtime)
    other = client(management_runtime, user=MediaTestUser(actor="auth0|other"))
    path = f"/media/{identifier}?fragment=K.1"
    assert (
        other.simulate_patch(
            path, json={"caption": "Stolen"}, headers=if_match(99)
        ).status_code
        == 403
    )
    assert (
        owner.simulate_post(
            f"/media/{identifier}/publish?fragment=K.1", json={}
        ).status_code
        == 403
    )
    assert (
        _manager(management_runtime)
        .simulate_post(
            f"/media/{identifier}/publish?fragment=K.3", json={}, headers=if_match(0)
        )
        .status_code
        == 404
    )


def test_primary_and_remove_verify_optional_if_match(
    management_runtime, media_database
):
    _, manager, identifier = _pending_upload(management_runtime)
    published = manager.simulate_post(
        f"/media/{identifier}/publish?fragment=K.1", json={}, headers=if_match(0)
    )
    assert published.status_code == 200, published.text
    primary_path = f"/media/{identifier}/primary?fragment=K.1"
    assert (
        manager.simulate_post(primary_path, json={}, headers=if_match(0)).status_code
        == 412
    )
    primary = manager.simulate_post(primary_path, json={}, headers=if_match(1))
    assert primary.status_code == 200, primary.text
    assert primary.json["media"][0]["revision"] == 2
    assert (
        manager.simulate_delete(
            f"/media/{identifier}?fragment=K.1", headers=if_match(1)
        ).status_code
        == 412
    )
    assert (
        manager.simulate_delete(
            f"/media/{identifier}?fragment=K.1", headers=if_match(2)
        ).status_code
        == 204
    )
    document = media_database.media.find_one({"_id": identifier})
    assert document["state"] == "deleted"
    assert document["revision"] == 3


def test_legacy_document_without_revision_reads_as_zero(
    management_runtime, media_database
):
    legacy = photo_media()
    management_runtime.management.repository.create(stored_media(legacy))
    media_database.media.update_one(
        {"_id": str(legacy.id)}, {"$unset": {"revision": ""}}
    )
    assert "revision" not in media_database.media.find_one({"_id": str(legacy.id)})
    manager = _manager(management_runtime)

    assert _listed(manager, str(legacy.id))["revision"] == 0
    response = manager.simulate_patch(
        f"/media/{legacy.id}?fragment=K.1",
        json={"caption": "Annotated"},
        headers=if_match(0),
    )
    assert response.status_code == 200, response.text
    assert response.json["media"][0]["revision"] == 1
    assert media_database.media.find_one({"_id": str(legacy.id)})["revision"] == 1


def test_contributors_do_not_see_revisions_of_legacy_items(management_runtime):
    legacy = photo_media()
    management_runtime.management.repository.create(stored_media(legacy))
    item = _listed(client(management_runtime), str(legacy.id))
    assert "revision" not in item


def test_review_preflight_accepts_if_match(management_runtime):
    app = falcon.App(
        cors_enable=True,
        middleware=[FalconAuthMiddleware(NoneAuthBackend(Guest))],
    )
    create_media_routes(app, cast(FragmentRepository, Fragments()), management_runtime)
    response = testing.TestClient(app).simulate_options(
        "/media/550e8400-e29b-41d4-a716-446655440000/publish?fragment=K.1",
        headers={
            "Origin": "https://www.ebl.lmu.de",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type, if-match",
        },
    )
    assert response.status_code == 200
    assert "if-match" in response.headers["Access-Control-Allow-Headers"].lower()
