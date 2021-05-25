import falcon

from ebl.context import Context
from ebl.files.web.files import PublicFilesResource


def create_files_route(api: falcon.API, context: Context):
    files = PublicFilesResource(context.public_file_repository)
    api.add_route("/images/{file_name}", files)
