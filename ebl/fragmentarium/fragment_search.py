import falcon
from ebl.require_scope import require_scope


class FragmentSearch:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp):
        if 'number' in req.params:
            resp.media = self._fragmentarium.search(req.params['number'])
        else:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
