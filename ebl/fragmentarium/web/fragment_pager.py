import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


class FragmentPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, number):

        resp.media = (self._finder
                      .fragment_pager(number))
