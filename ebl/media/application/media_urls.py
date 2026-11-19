from urllib.parse import quote

from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def fragment_media_url(fragment_id: MuseumNumber) -> str:
    return f"/media?fragment={quote(str(fragment_id), safe='')}"


def _representation_url(
    fragment_id: MuseumNumber, media_id: MediaId, representation: str
) -> str:
    return (
        f"/media/{media_id}/{representation}"
        f"?fragment={quote(str(fragment_id), safe='')}"
    )


def fragment_media_original_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return _representation_url(fragment_id, media_id, "file")


def fragment_media_display_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return _representation_url(fragment_id, media_id, "display")


def fragment_media_thumbnail_url(
    fragment_id: MuseumNumber, media_id: MediaId, size: ThumbnailSize
) -> str:
    return _representation_url(fragment_id, media_id, f"thumbnail/{size.value}")


def legacy_fragment_thumbnail_url(
    fragment_id: MuseumNumber, size: ThumbnailSize
) -> str:
    return f"/fragments/{fragment_id}/thumbnail/{size.value}"
