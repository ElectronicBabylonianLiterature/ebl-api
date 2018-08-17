import json
import falcon
from ebl.require_scope import require_scope


EBL_NAME = 'https://ebabylon.org/eblName'


class FragmentsResource:
    def __init__(self, fragmentarium, fetch_user_profile):
        self._fragmentarium = fragmentarium
        self._fetch_user_profile = fetch_user_profile

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, _req, resp, number):
        try:
            resp.media = self._fragmentarium.find(number)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'transliterate:fragments')
    def on_post(self, req, resp, number):
        user_profile = self._fetch_user_profile(req)

        try:
            transliteration = json.loads(req.stream.read())
            self._fragmentarium.update_transliteration(
                number,
                transliteration,
                user_profile
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
