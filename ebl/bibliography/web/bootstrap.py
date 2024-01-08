import falcon

from ebl.bibliography.web.bibliography_entries import (
    BibliographyEntriesResource,
    BibliographyResource,
    BibliographyAll,
    BibliographyList,
)
from ebl.context import Context


def create_bibliography_routes(api: falcon.App, context: Context):
    bibliography = context.get_bibliography()
    bibliography_resource = BibliographyResource(bibliography)
    bibliography_entries = BibliographyEntriesResource(bibliography)
    bibliography_all = BibliographyAll(bibliography)
    bibliography_list = BibliographyList(bibliography, context.cache)

    api.add_route("/bibliography", bibliography_resource)
    api.add_route("/bibliography/all", bibliography_all)
    api.add_route("/bibliography/list", bibliography_list)
    api.add_route("/bibliography/{id_}", bibliography_entries)
