import falcon

from ebl.context import Context
from ebl.signs.web.sign_search import SignsSearch
from ebl.signs.web.signs import SignsResource


def create_signs_routes(api: falcon.API, context: Context):
    signs_search = SignsSearch(context.sign_repository)
    signs = SignsResource(context.sign_repository)
    api.add_route("/signs", signs_search)
    api.add_route("/signs/{object_id}", signs)
