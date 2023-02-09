import falcon
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.domain.folios import Folio
from ebl.users.web.require_scope import require_folio_scope


class FoliosResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_folio_scope)
    def on_get(self, req: Request, resp: Response, name: str, number: str):
        file = self._finder.find_folio(Folio(name, number))

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
