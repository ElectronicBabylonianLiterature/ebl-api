import falcon
from falcon import Response, Request

from ebl.files.application.file_repository import FileRepository
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


def check_folio_scope(user: User, name: str):
    scope = f'read:{name}-folios'
    if not user.has_scope(scope):
        raise falcon.HTTPForbidden()


class FoliosResource:

    def __init__(self, files: FileRepository):
        self._files = files

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req: Request, resp: Response, name: str, number: str):
        """---
        description: Gets the folio image.
        responses:
          200:
            description: The folio image
            content:
              image/jpeg:
                schema:
                  type: string
                  format: binary
          404:
            description: The image does not exists
        security:
        - auth0:
          - read:fragments
          - read:MJG-folios
          - read:WGL-folios
          - read:FWG-folios
          - read:EL-folios
          - read:AKG-folios
        parameters:
        - in: path
          name: name
          description: Folio author abbreviation
          required: true
          schema:
            type: string
        - in: path
          name: number
          description: Folio number
          required: true
          schema:
            type: string
        """
        file_name = f'{name}_{number}.jpg'
        file = self._files.query_by_file_name(file_name)

        check_folio_scope(req.context.user, name)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
