from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.media.application.media_errors import MediaNotFoundError
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def parse_media_id(value: str) -> MediaId:
    try:
        return MediaId(value)
    except ValueError as error:
        raise DataError(f"Invalid media id: {value}") from error


def parse_thumbnail_size(value: str) -> ThumbnailSize:
    try:
        return ThumbnailSize(value)
    except ValueError as error:
        raise DataError(f"Unknown thumbnail size: {value}") from error


class MediaResource:
    def __init__(self, service: MediaService, finder: FragmentFinder) -> None:
        self._service = service
        self._finder = finder

    def _stored_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> StoredMedia:
        stored_media = self._service.get_stored_fragment_media(fragment_id, media_id)
        if stored_media is None:
            raise MediaNotFoundError(media_id)
        return stored_media
