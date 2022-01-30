import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_pager_info_schema import (
    FragmentPagerInfoSchema,
)
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.users.web.require_scope import require_scope


class FragmentPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req, resp, number):
        pager_elements = self._finder.fragment_pager(parse_museum_number(number))
        resp.media = FragmentPagerInfoSchema().dump(pager_elements)
