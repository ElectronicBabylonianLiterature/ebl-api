import falcon
from ebl.require_scope import require_scope


class FolioPagerResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, _req, resp, folio_name, folio_number, number):
        try:
            resp.media = (self
                          ._fragmentarium
                          .folio_pager(folio_name, folio_number, number))
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
