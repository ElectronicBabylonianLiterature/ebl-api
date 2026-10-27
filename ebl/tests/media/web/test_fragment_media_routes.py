from typing import Callable

import pytest
from falcon import testing

from ebl.context import Context
from ebl.media.application.media_stored import StoredMedia
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.media.web.helpers import body, get
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize(
    "svg,has_photo,media_type", [(False, True, "PHOTO"), (True, False, "COPY")]
)
def test_new_media_is_discoverable_in_details_and_search(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    svg: bool,
    has_photo: bool,
    media_type: str,
) -> None:
    create_media("K.100", svg=svg)
    detail = get(media_client, "/fragments/K.100")
    search = get(media_client, "/fragments/query?number=K.100&limit=1")
    assert detail.status_code == search.status_code == 200
    for document in (body(detail), body(search)["items"][0]):
        assert document["hasPhoto"] is has_photo
        assert document["legacyHasPhoto"] is False
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
        assert document["legacyHasPhoto"] is True
        assert document["mediaSummary"] == {"count": 0, "types": []}
        assert document["thumbnailPath"] == "/fragments/K.1/thumbnail/small"


def test_partial_copy_migration_keeps_explicit_legacy_availability(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    create_media("K.1", svg=True)
    result = get(media_client, "/fragments/K.1")
    assert result.status_code == 200
    assert body(result)["legacyHasPhoto"] is True
    assert body(result)["mediaSummary"]["types"] == ["COPY"]
