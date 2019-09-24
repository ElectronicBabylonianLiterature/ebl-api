import falcon

from ebl.require_scope import require_scope


class FolioPagerResource:
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, folio_name, folio_number, number):

        if req.context.user.can_read_folio(folio_name):
            resp.media = (self
                          ._fragmentarium
                          .folio_pager(folio_name, folio_number, number))
        else:
            raise falcon.HTTPForbidden()
