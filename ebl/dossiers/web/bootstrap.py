import falcon
from ebl.context import Context

from ebl.dossiers.web.dossier_records import (
    DossiersResource,
    DossiersSearchResource,
    DossiersFilterResource,
)


def create_dossiers_routes(api: falcon.App, context: Context):
    dossier_resource = DossiersResource(context.dossiers_repository)
    dossiers_search_resource = DossiersSearchResource(context.dossiers_repository)
    dossiers_filter_resource = DossiersFilterResource(context.dossiers_repository)
    api.add_route("/dossiers", dossier_resource)
    api.add_route("/dossiers/search", dossiers_search_resource)
    api.add_route("/dossiers/filter", dossiers_filter_resource)
