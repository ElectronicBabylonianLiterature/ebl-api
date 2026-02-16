from typing import Optional
import falcon
from falcon import Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder, ThumbnailSize
from ebl.users.web.require_scope import require_fragment_read_scope


class PhotoResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_fragment_read_scope)
    def on_get(
        self, _req, resp: Response, number: str, resolution: Optional[str] = None
    ):
        if resolution is None:
            file = self._finder.find_photo(number)
        else:
            width = ThumbnailSize.from_string(resolution)
            file = self._finder.find_thumbnail(number, width)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
