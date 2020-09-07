import falcon  # pyre-ignore
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: Request, resp: Response, number: str):  # pyre-ignore[11]
        """---
        description: Gets the fragment with given number,
        responses:
          200:
            description: The fragment
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Fragment'
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: path
          name: number
          schema:
            type: string
        """
        user: User = req.context.user
        fragment, has_photo = self._finder.find(number)
        resp.media = create_response_dto(fragment, user, has_photo)
