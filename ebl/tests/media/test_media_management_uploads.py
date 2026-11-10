import hashlib
from dataclasses import dataclass
import io
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import cast
from urllib.parse import quote

import attr
import falcon
import pytest
from falcon import testing
from PIL import Image

from ebl import error_handler
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.web.bootstrap import create_media_routes
from ebl.media.application.media_management_requests import MediaMutationRequest
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.infrastructure.auth0 import Auth0User

METADATA = {
    "originalFilename": "tablet.png",
    "type": "PHOTO",
    "caption": "Tablet obverse",
    "sourceInstitution": "Test museum",
    "rightsStatement": "Permission for eBL reproduction",
    "permissionAttested": True,
    "creator": "Photographer",
    "copyrightHolder": "Test museum",
}


def png(color="red"):
    output = io.BytesIO()
    Image.new("RGB", (800, 400), color).save(output, "PNG")
    return output.getvalue()


class Fragments:
    def query_read_scopes(self, number):
        if str(number) == "K.404":
            from ebl.errors import NotFoundError

            raise NotFoundError()
        return [Scope.READ_CAIC_FRAGMENTS] if str(number) == "K.2" else []


@dataclass(frozen=True)
class MediaTestUser:
    actor: str = "auth0|contributor"
    manager: bool = False
    contributor: bool = True
    fragment_access: bool = False


DEFAULT_MEDIA_TEST_USER = MediaTestUser()


def client(runtime, *, user: MediaTestUser = DEFAULT_MEDIA_TEST_USER):
    actor, manager = user.actor, user.manager
    contributor, fragment_access = user.contributor, user.fragment_access
    scopes = []
    if manager:
        scopes.append("manage:fragment_media")
    if contributor:
        scopes.append("upload:fragment_media")
    if fragment_access:
        scopes.append("read:CAIC-fragments")
    authenticated_user = Auth0User(
        {"sub": actor, "scope": " ".join(scopes)}, lambda: {"name": "Test"}
    )

    class Auth:
        def process_request(self, req, resp):
            req.context["user"] = authenticated_user

    api = falcon.App(middleware=[Auth()])
    error_handler.set_up(api)
    create_media_routes(api, cast(FragmentRepository, Fragments()), runtime)
    return testing.TestClient(api)


def if_match(revision):
    return {"If-Match": f'"{revision}"'}


def upload(api, metadata=None, content=None, key=None, fragment="K.1"):
    return api.simulate_post(
        "/media",
        params={"fragment": fragment},
        body=png() if content is None else content,
        headers={
            "Content-Type": "image/png",
            "Idempotency-Key": key or str(uuid.uuid4()),
            "X-Media-Metadata": quote(
                json.dumps(METADATA if metadata is None else metadata)
            ),
        },
    )


def test_upload_publication_gallery_original_and_tombstone(
    management_runtime, media_database
):
    contributor = client(management_runtime)
    manager = client(
        management_runtime,
        user=MediaTestUser(actor="auth0|manager", manager=True, contributor=False),
    )
    reader = client(management_runtime, user=MediaTestUser(contributor=False))
    original = png()
    response = upload(contributor, content=original)
    assert response.status_code == 201, response.text
    item = response.json["media"][0]
    assert item["publicationStatus"] == "PENDING_REVIEW"
    assert item["uploaderId"] == "auth0|contributor"
    identifier = item["id"]
    assert reader.simulate_get("/media?fragment=K.1").json == {"media": []}
    for representation in ("file", "display", "thumbnail/small"):
        assert (
            reader.simulate_get(
                f"/media/{identifier}/{representation}?fragment=K.1"
            ).status_code
            == 404
        )
    assert (
        contributor.simulate_get("/media?fragment=K.1&view=management").json["media"][
            0
        ]["id"]
        == identifier
    )
    assert (
        contributor.simulate_get(f"/media/{identifier}/file?fragment=K.1").content
        == original
    )
    document = media_database.media.find_one({"_id": identifier})
    assert (
        document["representations"]["original"]["representation"]["checksum"]
        == hashlib.sha256(original).hexdigest()
    )
    assert media_database["photos.files"].count_documents({}) == 0
    assert (
        manager.simulate_post(
            f"/media/{identifier}/publish?fragment=K.1",
            json={},
            headers=if_match(item["revision"]),
        ).status_code
        == 200
    )
    published = reader.simulate_get("/media?fragment=K.1").json["media"][0]
    assert published["publicationStatus"] == "PUBLISHED"
    for size in ("small", "medium", "large"):
        thumb = reader.simulate_get(
            published["representations"]["thumbnails"][size]["url"]
        )
        assert thumb.status_code == 200
        assert Image.open(io.BytesIO(thumb.content)).format == "JPEG"
    assert (
        reader.simulate_get(published["representations"]["original"]["url"]).content
        == original
    )
    assert manager.simulate_post(
        f"/media/{identifier}/primary?fragment=K.1", json={}
    ).json["media"][0]["isPrimary"]
    assert (
        len(management_runtime.service.list_fragment_media(MuseumNumber.of("K.1"))) == 1
    )
    files_before = media_database["media.files"].count_documents({})
    assert (
        manager.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 204
    )
    assert reader.simulate_get("/media?fragment=K.1").json == {"media": []}
    assert media_database["media.files"].count_documents({}) == files_before
    assert media_database.media.find_one({"_id": identifier})["state"] == "deleted"
    assert media_database.changelog.count_documents({"resource_type": "media"}) == 4


@pytest.mark.parametrize("fragment,expected", [("K.1", 403), ("K.2", 403)])
def test_readers_cannot_upload(management_runtime, fragment, expected):
    assert (
        upload(
            client(management_runtime, user=MediaTestUser(contributor=False)),
            fragment=fragment,
        ).status_code
        == expected
    )


def test_contributor_inaccessible_fragment(management_runtime):
    assert upload(client(management_runtime), fragment="K.2").status_code == 403
    assert upload(client(management_runtime), fragment="K.404").status_code == 404


def test_contributor_and_cross_fragment_permissions(management_runtime):
    owner = client(management_runtime)
    other = client(management_runtime, user=MediaTestUser(actor="auth0|other"))
    manager = client(management_runtime, user=MediaTestUser(manager=True))
    item = upload(owner).json["media"][0]
    path = f"/media/{item['id']}"
    assert other.simulate_get("/media?fragment=K.1&view=management").json == {
        "media": []
    }
    assert other.simulate_get(path + "/file?fragment=K.1").status_code == 404
    assert (
        other.simulate_patch(
            path + "?fragment=K.1", json={"caption": "Stolen"}
        ).status_code
        == 403
    )
    assert (
        owner.simulate_post(path + "/publish?fragment=K.1", json={}).status_code == 403
    )
    assert owner.simulate_delete(path + "?fragment=K.1").status_code == 403
    assert (
        owner.simulate_patch(
            path + "?fragment=K.1", json={"rightsStatement": "Changed"}
        ).status_code
        == 403
    )
    assert (
        owner.simulate_patch(path + "?fragment=K.1", json={"caption": "Edited"}).json[
            "media"
        ][0]["caption"]
        == "Edited"
    )
    assert (
        manager.simulate_post(path + "/primary?fragment=K.1", json={}).status_code
        == 409
    )
    assert (
        manager.simulate_post(path + "/publish?fragment=K.3", json={}).status_code
        == 404
    )
    assert (
        manager.simulate_patch(
            path + "?fragment=K.3", json={"caption": "Wrong"}
        ).status_code
        == 404
    )
    assert (
        manager.simulate_post(
            path + "/reject?fragment=K.1",
            json={"reason": "No permission evidence"},
            headers=if_match(1),
        ).status_code
        == 200
    )
    assert (
        owner.simulate_get("/media?fragment=K.1&view=management").json["media"][0][
            "reviewReason"
        ]
        == "No permission evidence"
    )
    assert (
        owner.simulate_patch(
            path + "?fragment=K.1", json={"caption": "Edited again"}
        ).status_code
        == 403
    )
    assert management_runtime.service.list_fragment_media(MuseumNumber.of("K.1")) == ()


def test_idempotent_retry_and_metadata_mismatch(management_runtime, media_database):
    api = client(management_runtime)
    key = str(uuid.uuid4())
    first = upload(api, key=key)
    retry = upload(api, key=key)
    assert retry.status_code == 200
    assert retry.json == first.json
    assert media_database["media.files"].count_documents({}) == 5
    assert (
        upload(api, key=key, metadata={**METADATA, "caption": "Different"}).status_code
        == 409
    )
    assert upload(api, key=key, content=png("blue")).status_code == 409
    assert media_database.media.count_documents({}) == 1


@pytest.mark.parametrize(
    "metadata",
    [
        {**METADATA, "permissionAttested": False},
        {**METADATA, "rightsStatement": ""},
        {**METADATA, "caption": " "},
        {**METADATA, "publicationStatus": "PUBLISHED"},
        {**METADATA, "uploaderId": "auth0|other"},
        {**METADATA, "type": "SVG"},
        {**METADATA, "originalFilename": "../secret.png"},
        {**METADATA, "projects": ["unknown"]},
    ],
)
def test_invalid_metadata_rejected(management_runtime, metadata):
    assert upload(client(management_runtime), metadata=metadata).status_code == 422


def test_invalid_binary_and_oversize(management_runtime):
    api = client(management_runtime)
    assert upload(api, content=b"fake png").status_code == 422
    assert upload(api, content=b"0" * (1024 * 1024 + 1)).status_code == 413


def test_disabled_write_routes(management_runtime):
    api = client(
        attr.evolve(management_runtime, management=None),
        user=MediaTestUser(manager=True),
    )
    assert upload(api).status_code == 404
    assert api.simulate_get("/media?fragment=K.1").status_code == 200
    assert api.simulate_get("/media?fragment=K.1&view=management").status_code == 404


def test_concurrent_primary_selection(management_runtime):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    identifiers = [upload(api).json["media"][0]["id"] for _ in range(3)]
    for identifier in identifiers:
        assert (
            api.simulate_post(
                f"/media/{identifier}/publish?fragment=K.1",
                json={},
                headers=if_match(0),
            ).status_code
            == 200
        )
    number = MuseumNumber.of("K.1")
    from ebl.media.domain import MediaId

    def select(identifier):
        return management_runtime.management.mutate(
            MediaMutationRequest(
                number,
                MediaId(identifier),
                "auth0|manager",
                True,
                "primary",
                {},
                lambda media: None,
            )
        )

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(select, identifiers))
    assert (
        sum(
            item.association_for(number).is_primary
            for item in management_runtime.service.list_fragment_media(number)
        )
        == 1
    )


def test_manager_only_scope_can_upload_then_explicitly_publish_own_submission(
    management_runtime,
):
    api = client(
        management_runtime,
        user=MediaTestUser(actor="auth0|manager", manager=True, contributor=False),
    )
    response = upload(api)
    assert response.status_code == 201
    item = response.json["media"][0]
    assert item["publicationStatus"] == "PENDING_REVIEW"
    number = MuseumNumber.of("K.1")
    assert management_runtime.service.find_media_by_fragments((number,))[number] == ()
    published = api.simulate_post(
        f"/media/{item['id']}/publish?fragment=K.1",
        json={},
        headers=if_match(item["revision"]),
    )
    assert published.status_code == 200
    assert published.json["media"][0]["reviewerId"] == "auth0|manager"
    assert (
        len(management_runtime.service.find_media_by_fragments((number,))[number]) == 1
    )
