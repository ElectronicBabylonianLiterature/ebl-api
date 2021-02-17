import falcon

from ebl.fragmentarium.application.folio_pager_schema import FolioPagerInfoSchema
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.web.dtos import parse_museum_number


class FolioPagerResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req, resp, folio_name, folio_number, number):
        """---
                description: Gets the next & previous folio in Database.
                responses:
                  200:
                    description: The fragmentnumber,name,folionumber of next & previous folio
                    content:
                      application/json:
                        schema:
                           $ref: '#/components/schemas/FolioPagerInfo'
                  404:
                    description: Could not retrieve any folios
                  422:
                    description: Invalid museum number
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
                  description: Museum number
                  required: true
                  schema:
                    type: string
                    pattern: '^.+?\\.[^.]+(\\.[^.]+)?$'
                """

        if req.context.user.can_read_folio(folio_name):
            folio = self._finder.folio_pager(
                folio_name, folio_number, parse_museum_number(number)
            )
            resp.media = FolioPagerInfoSchema().dump(folio)
        else:
            raise falcon.HTTPForbidden()
