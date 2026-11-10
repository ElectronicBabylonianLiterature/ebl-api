from typing import Optional
import falcon
from falcon import Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder, ThumbnailSize
from ebl.users.web.require_scope import require_fragment_read_scope
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_visibility import LegacyMediaVisibility
from ebl.fragmentarium.web.dtos import parse_museum_number


class PhotoResource:
    def __init__(
        self,
        finder: FragmentFinder,
        media: Optional[MediaService] = None,
        legacy_visibility: Optional[LegacyMediaVisibility] = None,
    ) -> None:
        self._finder = finder
        self._legacy_visibility = (
            legacy_visibility if legacy_visibility is not None else media
        )

    @falcon.before(require_fragment_read_scope)
    def on_get(
        self,
        _req: falcon.Request,
        resp: Response,
        number: str,
        resolution: Optional[str] = None,
    ) -> None:
        visibility = self._legacy_visibility
        if visibility is not None:
            resp.set_header("Cache-Control", "private, no-store")
            resp.set_header("Vary", "Authorization")
            resp.set_header("X-Content-Type-Options", "nosniff")
        if visibility is not None and not visibility.legacy_fallback_allowed(
            parse_museum_number(number)
        ):
            raise falcon.HTTPNotFound()
        if resolution is None:
            file = self._finder.find_photo(number)
        else:
            width = ThumbnailSize.from_string(resolution)
            file = self._finder.find_thumbnail(number, width)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
