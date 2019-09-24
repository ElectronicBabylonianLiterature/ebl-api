import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.require_scope import require_scope


class FragmentsResource:

    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, number):
        user = req.context.user
        fragment = self._finder.find(number)
        resp.media = {
            **fragment.to_dict_for(user),
            'atf': fragment.text.atf
        }
