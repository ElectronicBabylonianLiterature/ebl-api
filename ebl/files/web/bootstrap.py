import falcon

from ebl.context import Context
from ebl.files.web.files import create_files_resource


def create_files_route(api: falcon.API, context: Context, spec):
    files = create_files_resource(context.auth_backend)(context.files)
    api.add_route('/images/{file_name}', files)
    spec.path(resource=files)
