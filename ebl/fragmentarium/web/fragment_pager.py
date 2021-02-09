import falcon  # pyre-ignore

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_pager_schema import FragmentPagerInfoSchema
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.web.dtos import parse_museum_number


class FragmentPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req, resp, number):
        """---
        description: Gets the next & previous fragment in Database.
        responses:
          200:
            description: The number/_id of next & previous Fragment
            content:
              application/json:
                schema:
                   $ref: '#/components/schemas/FragmentPagerInfo'
          404:
            description: Could not retrieve any fragments
          422:
            description: Invalid museum number
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: path
          name: number
          description: Museum number
          required: true
          schema:
            type: string
            pattern: '^.+?\\.[^.]+(\\.[^.]+)?$'
        """

        fragment = self._finder.fragment_pager(parse_museum_number(number))
        resp.media = FragmentPagerInfoSchema().dump(fragment)
