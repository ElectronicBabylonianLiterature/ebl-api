import json
import falcon
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliterations import Transliteration


class FragmentsResource:
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, _req, resp, number):
        try:
            resp.media = self._fragmentarium.find(number).to_dict()
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'transliterate:fragments')
    def on_post(self, req, resp, number):
        def parse_request():
            body = json.loads(req.stream.read())
            try:
                return Transliteration(
                    body['transliteration'],
                    body['notes']
                )
            except (TypeError, KeyError):
                raise falcon.HTTPUnprocessableEntity()

        try:
            self._fragmentarium.update_transliteration(
                number,
                parse_request(),
                req.context['user']
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
