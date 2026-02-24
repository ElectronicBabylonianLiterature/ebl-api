import falcon
from falcon_caching import Cache
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_pager_info_schema import (
    FragmentPagerInfoSchema,
)
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.users.web.require_scope import require_fragment_read_scope


def make_fragment_pager_resource(finder: FragmentFinder, cache: Cache):
    class FragmentPagerResource:
        def __init__(self, finder: FragmentFinder):
            self._finder = finder

        @falcon.before(require_fragment_read_scope)
        def on_get(self, req, resp, number):
            pager_elements = self._finder.fragment_pager(parse_museum_number(number))
            resp.text = FragmentPagerInfoSchema().dumps(pager_elements)

    return FragmentPagerResource(finder)
