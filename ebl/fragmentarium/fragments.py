import falcon
from ebl.require_scope import require_scope


class FragmentsResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, number):
        user = req.context['user']
        fragment = self._fragmentarium.find(number)
        resp.media = {
            **fragment.to_dict_for(user),
            'atf': fragment.text.atf
        }
