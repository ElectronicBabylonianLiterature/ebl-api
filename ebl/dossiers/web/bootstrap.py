import falcon
from ebl.context import Context

from ebl.dossiers.web.dossier_records import (
    DossiersResource,
    DossierSearchResource,
)


def create_dossiers_routes(api: falcon.App, context: Context):
    dossier_resourse = DossiersResource(context.dossiers_repository)
    dossier_search_resource = DossierSearchResource(context.dossiers_repository)
    api.add_route("/dossiers", dossier_resourse)
    api.add_route("/dossiers/search", dossier_search_resource)
