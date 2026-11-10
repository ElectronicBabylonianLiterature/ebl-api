from dataclasses import dataclass
from threading import Thread
from wsgiref.simple_server import make_server

import attr
import falcon
import pytest
import requests
from falcon import testing
from pymongo.database import Database

from ebl.app import create_app
from ebl.context import Context
from ebl.media.application.media_runtime import MediaRuntime
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.media.factories import association
from ebl.tests.media.test_media_legacy_visibility_review import (
    LegacyMediaOptions,
    add_legacy,
    legacy_client,
)
from ebl.tests.media.test_media_management_uploads import if_match, png, upload
from ebl.tests.media.web.helpers import body
from ebl.transliteration.domain.museum_number import MuseumNumber


ROUTES = {
    "/fragments/K.100": None,
    "/fragments/query?number=K.100&limit=1": "items",
    "/fragments/retrieve-all": "fragments",
}


def fragment_document(payload: dict, collection: str | None) -> dict:
    if collection is None:
        return payload
    return next(
        row for row in payload[collection] if row["museumNumber"]["number"] == "100"
    )


@dataclass(frozen=True)
class SuppressedPhotoCase:
    application: falcon.App
    before_removal: dict[str, dict]
    managed_original: str


@pytest.fixture
def suppressed_photo_case(
    context: Context, management_runtime: MediaRuntime, database: Database
) -> SuppressedPhotoCase:
    number = MuseumNumber.of("K.100")
    context.fragment_repository.create(
        TransliteratedFragmentFactory.build(number=number, references=())
    )
    database["fragments"].update_one(
        {"_id": "K.100"}, {"$unset": {"authorizedScopes": ""}}
    )
    legacy_id, _, _ = add_legacy(
        management_runtime,
        database,
        LegacyMediaOptions(
            filename="K.100.jpg", associations=(association(fragment_id=number),)
        ),
    )
    manager = legacy_client(management_runtime, database, manager=True)
    uploaded = upload(manager, fragment="K.100")
    assert isinstance(uploaded, testing.Result)
    assert uploaded.status_code == 201, uploaded.text
    item = body(uploaded)["media"][0]
    published = manager.simulate_post(
        f"/media/{item['id']}/publish?fragment=K.100", json={}, headers=if_match(0)
    )
    assert isinstance(published, testing.Result)
    assert published.status_code == 200, published.text
    managed_original = body(published)["media"][0]["representations"]["original"]["url"]
    application = create_app(attr.evolve(context, media=management_runtime))
    client = testing.TestClient(application)
    before_removal = {}
    for path, collection in ROUTES.items():
        response = client.simulate_get(path)
        assert isinstance(response, testing.Result)
        assert response.status_code == 200, response.text
        payload = response.json
        assert isinstance(payload, dict)
        document = fragment_document(payload, collection)
        assert document["hasPhoto"] is True
        before_removal[path] = document
    removed = manager.simulate_delete(f"/media/{legacy_id}?fragment=K.100")
    assert isinstance(removed, testing.Result)
    assert removed.status_code == 204, removed.text
    return SuppressedPhotoCase(application, before_removal, managed_original)


def test_suppressed_legacy_photo_preserves_existing_fragment_contract_over_http(
    suppressed_photo_case: SuppressedPhotoCase,
) -> None:
    case = suppressed_photo_case
    with make_server("127.0.0.1", 0, case.application) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            for path, collection in ROUTES.items():
                response = requests.get(origin + path, timeout=10)
                assert response.status_code == 200, response.text
                document = fragment_document(response.json(), collection)
                assert document["hasPhoto"] is False
                assert "legacyHasPhoto" not in document
                original = case.before_removal[path]
                assert ("thumbnailPath" in document) == ("thumbnailPath" in original)
                assert document.get("thumbnailPath") == original.get("thumbnailPath")
                assert document["mediaSummary"]["count"] == 1
                assert document["mediaSummary"]["types"] == ["PHOTO"]
            legacy = requests.get(origin + "/fragments/K.100/photo", timeout=10)
            assert legacy.status_code == 404
            managed = requests.get(origin + case.managed_original, timeout=10)
            assert managed.status_code == 200
            assert managed.content == png()
        finally:
            server.shutdown()
            thread.join(timeout=10)
        assert not thread.is_alive()
