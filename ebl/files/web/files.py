from typing import Type

import falcon
from falcon import Response, Request
from falcon_auth import MultiAuthBackend, NoneAuthBackend
from falcon_auth.backends import AuthBackend

from ebl.auth0 import Guest, User
from ebl.files.application.file_repository import FileRepository, File


def check_scope(user: User, file: File):
    if not file.can_be_read_by(user):
        raise falcon.HTTPForbidden()


def create_files_resource(auth_backend: AuthBackend) -> Type:
    class FilesResource:

        auth = {
            'backend': MultiAuthBackend(
                auth_backend,
                NoneAuthBackend(Guest)
            )
        }

        def __init__(self, files: FileRepository):
            self._files = files

        def on_get(self, req: Request, resp: Response, file_name: str):
            file = self._files.query_by_file_name(file_name)

            check_scope(req.context.user, file)

            resp.content_type = file.content_type
            resp.content_length = file.length
            resp.stream = file

    return FilesResource
