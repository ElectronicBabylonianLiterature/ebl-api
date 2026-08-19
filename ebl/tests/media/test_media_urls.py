import pytest

from ebl.media.application.media_urls import (
    fragment_media_display_url,
    fragment_media_original_url,
    fragment_media_thumbnail_url,
    legacy_fragment_thumbnail_url,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber

MEDIA_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


@pytest.mark.parametrize(
    "fragment_id,encoded_fragment_id",
    [
        (MuseumNumber.of("K.123"), "K.123"),
        (MuseumNumber("A 123", "1"), "A%20123.1"),
        (MuseumNumber("A/B", "1"), "A%2FB.1"),
        (MuseumNumber("A%", "1"), "A%25.1"),
        (MuseumNumber("A?", "1"), "A%3F.1"),
        (MuseumNumber("A#", "1"), "A%23.1"),
        (MuseumNumber("Š", "1"), "%C5%A0.1"),
    ],
)
def test_fragment_media_original_url_encodes_fragment_path_segment(
    fragment_id: MuseumNumber, encoded_fragment_id: str
) -> None:
    assert fragment_media_original_url(fragment_id, MEDIA_ID) == (
        f"/fragments/{encoded_fragment_id}/media/{MEDIA_ID}/file"
    )


def test_fragment_media_display_url_encodes_fragment_path_segment() -> None:
    assert fragment_media_display_url(MuseumNumber("A/B", "1"), MEDIA_ID) == (
        f"/fragments/A%2FB.1/media/{MEDIA_ID}/display"
    )


def test_fragment_media_thumbnail_url_encodes_dynamic_path_segments() -> None:
    assert (
        fragment_media_thumbnail_url(
            MuseumNumber("A? 1", "1"), MEDIA_ID, ThumbnailSize.SMALL
        )
        == f"/fragments/A%3F%201.1/media/{MEDIA_ID}/thumbnail/small"
    )


def test_fragment_media_url_keeps_route_separators_structured() -> None:
    assert (
        fragment_media_thumbnail_url(
            MuseumNumber("A/B", "1"), MEDIA_ID, ThumbnailSize.MEDIUM
        )
        == f"/fragments/A%2FB.1/media/{MEDIA_ID}/thumbnail/medium"
    )


def test_media_uuid_and_thumbnail_size_remain_readable() -> None:
    assert (
        fragment_media_thumbnail_url(
            MuseumNumber.of("K.123"), MEDIA_ID, ThumbnailSize.LARGE
        )
        == f"/fragments/K.123/media/{MEDIA_ID}/thumbnail/large"
    )


def test_legacy_fragment_thumbnail_url_preserves_raw_thumbnail_path() -> None:
    assert (
        legacy_fragment_thumbnail_url(MuseumNumber("A/B", "1"), ThumbnailSize.SMALL)
        == "/fragments/A/B.1/thumbnail/small"
    )
