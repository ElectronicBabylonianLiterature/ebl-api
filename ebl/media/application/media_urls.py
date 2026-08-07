from urllib.parse import quote

from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def _path_segment(value) -> str:
    return quote(str(value), safe="")


def fragment_media_original_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/{_path_segment(media_id)}/file"
    )


def fragment_media_display_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/"
        f"{_path_segment(media_id)}/display"
    )


def fragment_media_thumbnail_url(
    fragment_id: MuseumNumber, media_id: MediaId, size: ThumbnailSize
) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/{_path_segment(media_id)}"
        f"/thumbnail/{_path_segment(size.value)}"
    )


def legacy_fragment_thumbnail_url(
    fragment_id: MuseumNumber, size: ThumbnailSize
) -> str:
    return f"/fragments/{fragment_id}/thumbnail/{size.value}"
