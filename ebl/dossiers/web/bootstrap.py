import falcon
from ebl.context import Context

from ebl.dossiers.web.dossier_records import (
    DossierResource,
)


def create_afo_register_routes(api: falcon.App, context: Context):
    dossier_resourse = DossierResource(context.dossier_repository)
    api.add_route("/dossiers", dossier_resourse)
