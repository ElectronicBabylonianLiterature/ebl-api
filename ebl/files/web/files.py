from falcon import Response
from falcon_auth import NoneAuthBackend

from ebl.files.application.file_repository import FileRepository
from ebl.users.domain.user import Guest


class PublicFilesResource:
    auth = {"backend": NoneAuthBackend(Guest)}

    def __init__(self, files: FileRepository):
        self._files = files

    def on_get(self, _req, resp: Response, file_name: str):
        file = self._files.query_by_file_name(file_name)

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
