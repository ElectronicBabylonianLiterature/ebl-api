import falcon
from falcon import Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


class PhotoResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, _req, resp: Response, number: str):
        file = self._finder.find_photo(number)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
