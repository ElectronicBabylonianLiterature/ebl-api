import uuid
from concurrent.futures import ThreadPoolExecutor
import attr
import pytest
from ebl.media.application.media_management_requests import MediaMutationRequest
from ebl.transliteration.domain.museum_number import MuseumNumber

from ebl.tests.media.test_media_management_uploads import (
    METADATA,
    MediaTestUser,
    client,
    upload,
    if_match,
    png,
)


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
