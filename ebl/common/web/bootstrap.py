import falcon

from ebl.context import Context
from ebl.common.web.provenances import (
    ProvenancesResource,
    ProvenanceResource,
    ProvenanceChildrenResource,
)


def create_common_routes(api: falcon.App, context: Context):
    provenances_resource = ProvenancesResource(context.provenance_repository)
    provenance_resource = ProvenanceResource(context.provenance_repository)
    provenance_children_resource = ProvenanceChildrenResource(
        context.provenance_repository
    )

    api.add_route("/provenances", provenances_resource)
    api.add_route("/provenances/{id_}", provenance_resource)
    api.add_route("/provenances/{id_}/children", provenance_children_resource)
