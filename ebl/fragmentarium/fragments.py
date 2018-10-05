import json
import falcon
from ebl.require_scope import require_scope


class FragmentsResource:
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, _req, resp, number):
        try:
            resp.media = self._fragmentarium.find(number)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'transliterate:fragments')
    def on_post(self, req, resp, number):
        try:
            updates = json.loads(req.stream.read())
            self._fragmentarium.update_transliteration(
                number,
                updates,
                req.context['user']
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
