import falcon
from falcon import Response

from ebl.files.application.file_repository import FileRepository
from ebl.users.web.require_scope import require_scope


class PhotoResource:

    def __init__(self, files: FileRepository):
        self._files = files

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, _req, resp: Response, number: str):
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
        file_name = f'{number}.jpg'
        file = self._files.query_by_file_name(file_name)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
