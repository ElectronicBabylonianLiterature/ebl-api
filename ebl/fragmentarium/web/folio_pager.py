import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


class FolioPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req, resp, folio_name, folio_number, number):
        """---
                description: Gets the next & previous folio in Database.
                responses:
                  200:
                    description: The number & name of Folio & number of fragment of
                    next & previous Folio
                    content:
                      application/json:
                        schema:
                           $ref: '#/components/schemas/FragmentPagerFolioInfo'
                  404:
                    description: Could not retrieve any fragments
                security:
                - auth0:
                  - read:fragments
                parameters:
                - in: path
                  name: folio_name
                  description: Folio name
                  required: true
                  - in: path
                  name: folio_number
                  description: Folio number
                  required: true
                  - in: path
                  name: number
                  description: Fragment number
                  required: true
                  schema:
                    type: string
                """

        if req.context.user.can_read_folio(folio_name):
            resp.media = self._finder.folio_pager(folio_name, folio_number, number)
        else:
            raise falcon.HTTPForbidden()
