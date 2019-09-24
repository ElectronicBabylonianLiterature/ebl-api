import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.require_scope import require_scope


class FolioPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, folio_name, folio_number, number):

        if req.context.user.can_read_folio(folio_name):
            resp.media = (self
                          ._finder
                          .folio_pager(folio_name, folio_number, number))
        else:
            raise falcon.HTTPForbidden()
