import falcon  # pyre-ignore[21]

from ebl.bibliography.web.bibliography_entries import (
    BibliographyEntriesResource,
    BibliographyResource,
)
from ebl.context import Context


def create_bibliography_routes(
    api: falcon.API, context: Context, spec  # pyre-ignore[11]
):
    bibliography = context.get_bibliography()
    bibliography_resource = BibliographyResource(bibliography)
    bibliography_entries = BibliographyEntriesResource(bibliography)
    api.add_route("/bibliography", bibliography_resource)
    api.add_route("/bibliography/{id_}", bibliography_entries)
    spec.path(resource=bibliography_resource)
    spec.path(resource=bibliography_entries)
