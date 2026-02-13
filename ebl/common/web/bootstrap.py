import falcon

from ebl.context import Context
from ebl.common.web.provenances import (
    ProvenancesResource,
    ProvenanceResource,
    ProvenanceChildrenResource,
)


def create_common_routes(api: falcon.App, context: Context):
    provenance_repository = context.provenance_repository
    routes = [
        ("/provenances", ProvenancesResource(provenance_repository)),
        ("/provenances/{id_}", ProvenanceResource(provenance_repository)),
        (
            "/provenances/{id_}/children",
            ProvenanceChildrenResource(provenance_repository),
        ),
    ]

    for uri, resource in routes:
        api.add_route(uri, resource)
