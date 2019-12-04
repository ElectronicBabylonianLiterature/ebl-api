import falcon, json

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


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
                security:
                - auth0:
                  - read:fragments
                parameters:
                - in: path
                  name: number
                  description: Fragment number
                  required: true
                  schema:
                    type: string
                """

        resp.media = json.dump(self._finder.fragment_pager(number))
