import falcon
import pytest

from ebl.fragmentarium.application.fragment_finder import ThumbnailSize


def test_get_photo(client, photo):
    result = client.simulate_get("/fragments/K.1/photo")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == photo.content_type
    assert result.content == photo.data


def test_get_photo_not_found(client):
    result = client.simulate_get("/fragments/unknown.42/photo")

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("resolution", [item.name.lower() for item in ThumbnailSize])
def test_get_thumbnail(client, photo, resolution: str):
    result = client.simulate_get(f"/fragments/K.1/thumbnail/{resolution}")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == photo.content_type
    assert result.content == photo.data


def test_get_thumbnail_not_found(client, photo):
    result = client.simulate_get("/fragments/K.99/thumbnail/small")
    assert result.status == falcon.HTTP_NOT_FOUND
