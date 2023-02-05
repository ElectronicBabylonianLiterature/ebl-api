import falcon

from ebl.fragmentarium.application.folio_pager_schema import FolioPagerInfoSchema
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.users.web.require_scope import require_scope


class FolioPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req, resp, folio_name, folio_number, number):
        if req.context.user.can_read_folio(folio_name):
            folio = self._finder.folio_pager(
                folio_name, folio_number, parse_museum_number(number)
            )
            resp.media = FolioPagerInfoSchema().dump(folio)
        else:
            raise falcon.HTTPForbidden()
