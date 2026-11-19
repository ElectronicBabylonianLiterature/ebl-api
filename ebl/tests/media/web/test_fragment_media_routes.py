from typing import Callable

import pytest
from falcon import testing
from pymongo.database import Database

from ebl.context import Context
from ebl.media.application.media_stored import StoredMedia
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.application.text_schema import TextSchema
from ebl.tests.factories.transliterated_fragment_text import (
    TRANSLITERATED_FRAGMENT_TEXT,
)
from ebl.tests.media.web.helpers import body, get
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize("svg,media_type", [(False, "PHOTO"), (True, "COPY")])
def test_new_media_is_discoverable_in_details_and_search(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    svg: bool,
    media_type: str,
) -> None:
    create_media("K.100", svg=svg)
    detail = get(media_client, "/fragments/K.100")
    search = get(media_client, "/fragments/query?number=K.100&limit=1")
    assert detail.status_code == search.status_code == 200
    for document in (body(detail), body(search)["items"][0]):
        assert document["hasPhoto"] is False
        assert "legacyHasPhoto" not in document
        assert document["mediaSummary"]["count"] == 1
        assert document["mediaSummary"]["types"] == [media_type]
        preview = document["mediaSummary"]["primary"]["thumbnail"]["url"]
        assert get(media_client, preview).content == b"preview"


def test_empty_media_keeps_legacy_photo_in_details_and_search(
    media_context: Context, media_client: testing.TestClient
) -> None:
    media_context.fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of("K.1"), references=())
    )
    detail = get(media_client, "/fragments/K.1")
    search = get(media_client, "/fragments/query?number=K.1&limit=1")
    assert detail.status_code == search.status_code == 200
    for document in (body(detail), body(search)["items"][0]):
        assert document["hasPhoto"] is True
        assert "legacyHasPhoto" not in document
        assert document["mediaSummary"] == {"count": 0, "types": []}
    assert "thumbnailPath" not in body(detail)
    assert body(search)["items"][0]["thumbnailPath"] == "/fragments/K.1/thumbnail/small"


def test_partial_copy_migration_keeps_explicit_legacy_availability(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    create_media("K.1", svg=True)
    result = get(media_client, "/fragments/K.1")
    assert result.status_code == 200
    assert body(result)["hasPhoto"] is True
    assert "legacyHasPhoto" not in body(result)
    assert body(result)["mediaSummary"]["types"] == ["COPY"]


def test_retrieve_all_preserves_absent_legacy_thumbnail(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    database: Database,
) -> None:
    create_media("K.100")
    database["fragments"].update_one(
        {"_id": "K.100"},
        {
            "$unset": {"authorizedScopes": ""},
            "$set": {"text": TextSchema().dump(TRANSLITERATED_FRAGMENT_TEXT)},
        },
    )
    response = get(media_client, "/fragments/retrieve-all")
    assert response.status_code == 200
    document = next(
        item
        for item in body(response)["fragments"]
        if item["museumNumber"]["number"] == "100"
    )
    assert document["hasPhoto"] is False
    assert "thumbnailPath" not in document
    assert "legacyHasPhoto" not in document
    assert document["mediaSummary"]["count"] == 1
