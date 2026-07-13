from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def fragment_media_original_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return f"/fragments/{fragment_id}/media/{media_id}/file"


def fragment_media_display_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return f"/fragments/{fragment_id}/media/{media_id}/display"


def fragment_media_thumbnail_url(
    fragment_id: MuseumNumber, media_id: MediaId, size: ThumbnailSize
) -> str:
    return f"/fragments/{fragment_id}/media/{media_id}/thumbnail/{size.value}"


def fragment_thumbnail_url(fragment_id: MuseumNumber, size: ThumbnailSize) -> str:
    return f"/fragments/{fragment_id}/thumbnail/{size.value}"
