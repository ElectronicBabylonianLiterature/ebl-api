import falcon
from falcon_auth import MultiAuthBackend
from falcon_auth import NoneAuthBackend
from ebl.auth0 import Guest


def check_scope(user, grid_out):
    file_scope = (grid_out.metadata or {}).get('scope')
    if (
            file_scope and
            not user.has_scope(f'read:{file_scope}')
    ):
        raise falcon.HTTPForbidden()


def create_files_resource(auth_backend):
    class FilesResource:
        # pylint: disable=R0903
        auth = {
            'backend': MultiAuthBackend(
                auth_backend,
                NoneAuthBackend(Guest)
            )
        }

        def __init__(self, files):
            self._files = files

        def on_get(self, req, resp, file_name):
            grid_out = self._files.find(file_name)

            check_scope(req.context['user'], grid_out)

            resp.content_type = grid_out.content_type
            resp.stream_len = grid_out.length
            resp.stream = grid_out

    return FilesResource
