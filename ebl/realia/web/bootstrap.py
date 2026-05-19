import falcon

from ebl.context import Context
from ebl.realia.web.realia import RealiaResource, RealiaSearchResource


def create_realia_routes(api: falcon.App, context: Context) -> None:
    realia_resource = RealiaResource(context.realia_repository)
    realia_search_resource = RealiaSearchResource(context.realia_repository)
    api.add_route("/realia/{realia_id}", realia_resource)
    api.add_route("/realia", realia_search_resource)
