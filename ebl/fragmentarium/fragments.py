import falcon
from ebl.require_scope import require_scope


class FragmentsResource:
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, number):
        user = req.context['user']
        resp.media = (self
                      ._fragmentarium
                      .find(number)
                      .to_dict_for(user))

    def on_post(self, _req, _resp, number):
        # pylint: disable=R0201
        raise falcon.HTTPPermanentRedirect(f'{number}/transliteration')
