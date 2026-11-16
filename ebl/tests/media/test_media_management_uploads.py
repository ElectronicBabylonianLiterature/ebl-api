import hashlib
from dataclasses import dataclass
import io
import json
import uuid
from typing import Protocol, cast
from urllib.parse import quote

import falcon
from falcon import testing
from PIL import Image

from ebl import error_handler
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.web.bootstrap import create_media_routes
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


class MediaTestResult(Protocol):
    status_code: int
    text: str
    content: bytes
    headers: dict[str, str]
    json: dict


class MediaTestClient(Protocol):
    def simulate_get(self, path: str = "/", **kwargs: object) -> MediaTestResult: ...

    def simulate_post(self, path: str = "/", **kwargs: object) -> MediaTestResult: ...

    def simulate_patch(self, path: str = "/", **kwargs: object) -> MediaTestResult: ...

    def simulate_delete(self, path: str = "/", **kwargs: object) -> MediaTestResult: ...

    def simulate_options(
        self, path: str = "/", **kwargs: object
    ) -> MediaTestResult: ...


def client(
    runtime, *, user: MediaTestUser = DEFAULT_MEDIA_TEST_USER
) -> MediaTestClient:
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
    return cast(MediaTestClient, testing.TestClient(api))


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
