from typing import Callable

import pytest
from falcon import testing

from ebl.tests.media.web.helpers import body, get

from ebl.media.application.media_stored import StoredMedia
from ebl.media.application.media_urls import fragment_media_url
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize("number", ["K.1", "A/B.1", "A %.1", "Š?#.1"])
def test_media_urls_round_trip_through_falcon(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    number: str,
) -> None:
    create_media(number)
    response = get(media_client, fragment_media_url(MuseumNumber.of(number)))
    assert response.status_code == 200
    [media] = body(response)["media"]
    representations = media["representations"]
    for representation, content in (
        (representations["original"], b"original"),
        (representations["display"], b"preview"),
        (representations["thumbnails"]["small"], b"preview"),
    ):
        binary = get(media_client, representation["url"])
        assert binary.status_code == 200
        assert binary.content == content
        assert binary.headers["content-type"] == representation["mimeType"]
        assert binary.headers["content-length"] == str(len(content))
        assert binary.headers["cache-control"] == "private, no-store"
        assert binary.headers["x-content-type-options"] == "nosniff"
        assert "Authorization" in binary.headers["vary"]
    assert "importSource" not in media
    assert "originalFilename" not in media


def test_svg_is_download_only(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    create_media(svg=True)
    [media] = body(get(media_client, "/media?fragment=K.1"))["media"]
    response = get(media_client, media["representations"]["original"]["url"])
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["content-security-policy"] == "sandbox; default-src 'none'"


@pytest.mark.parametrize("representation", ["display", "thumbnail/small"])
def test_optional_representation_is_not_found(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    representation: str,
) -> None:
    stored = create_media(previews=False)
    response = get(
        media_client, f"/media/{stored.media.id}/{representation}?fragment=K.1"
    )
    assert response.status_code == 404


@pytest.mark.parametrize("suffix", ["thumbnail/huge", "thumbnail"])
def test_invalid_thumbnail_size_is_unprocessable(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    suffix: str,
) -> None:
    stored = create_media()
    response = get(media_client, f"/media/{stored.media.id}/{suffix}?fragment=K.1")
    assert response.status_code == 422


def test_unknown_representation_is_not_found(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    stored = create_media()
    response = get(media_client, f"/media/{stored.media.id}/secret?fragment=K.1")
    assert response.status_code == 404


def test_disabled_media_routes_preserve_legacy_photo(
    client: testing.TestClient,
) -> None:
    assert get(client, "/media?fragment=K.1").status_code == 404
    assert get(client, "/fragments/K.1/photo").status_code == 200
