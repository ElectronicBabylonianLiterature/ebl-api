import falcon  # pyre-ignore
from falcon import Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.users.web.require_scope import require_scope


class PhotoResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, _req, resp: Response, number: str):  # pyre-ignore[11]
        """---
        description: Gets the photo of the fragment.
        responses:
          200:
            description: The photo of the fragment
            content:
              image/jpeg:
                schema:
                  type: string
                  format: binary
          404:
            description: The photo does not exists
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
        file = self._finder.find_photo(FragmentNumber(number))

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
