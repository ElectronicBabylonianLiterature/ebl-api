from falcon import Response
from falcon_auth import NoneAuthBackend

from ebl.files.application.file_repository import FileRepository
from ebl.users.domain.user import Guest


class PublicFilesResource:

    auth = {
        'backend': NoneAuthBackend(Guest)
    }

    def __init__(self, files: FileRepository):
        self._files = files

    def on_get(self, _req, resp: Response, file_name: str):
        """---
        description: Gets an image.
        responses:
          200:
            description: The image
            content:
              image/jpeg:
                schema:
                  type: string
                  format: binary
              image/svg+xml:
                schema:
                  type: string
                  format: binary
          404:
            description: The image does not exists
        parameters:
        - in: path
          name: file_name
          description: Image file name
          required: true
          schema:
            type: string
        """
        file = self._files.query_by_file_name(file_name)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
