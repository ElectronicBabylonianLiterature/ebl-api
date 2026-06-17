import falcon

from ebl.bibliography.web.bibliography_entries import (
    BibliographyEntriesResource,
    BibliographyResource,
    BibliographyAll,
    BibliographyDuplicateCandidatesResource,
    BibliographyList,
    PartnerBibliographyDuplicateOverrideResource,
    PartnerBibliographyEntryResource,
    PartnerBibliographyResource,
)
from ebl.context import Context


def create_bibliography_routes(api: falcon.App, context: Context):
    bibliography = context.get_bibliography()
    bibliography_resource = BibliographyResource(bibliography)
    bibliography_entries = BibliographyEntriesResource(bibliography)
    bibliography_all = BibliographyAll(bibliography)
    bibliography_list = BibliographyList(bibliography, context.cache)
    duplicate_candidates = BibliographyDuplicateCandidatesResource(bibliography)
    partner_bibliography = PartnerBibliographyResource(bibliography)
    partner_bibliography_duplicate_override = (
        PartnerBibliographyDuplicateOverrideResource(bibliography)
    )
    partner_bibliography_entry = PartnerBibliographyEntryResource(bibliography)

    api.add_route("/bibliography", bibliography_resource)
    api.add_route("/bibliography/all", bibliography_all)
    api.add_route("/bibliography/list", bibliography_list)
    api.add_route("/bibliography/{id_}", bibliography_entries)
    api.add_route("/api/v1/bibliography/duplicate-candidates", duplicate_candidates)
    api.add_route("/api/v1/bibliography", partner_bibliography)
    api.add_route(
        "/api/v1/bibliography/duplicate-override",
        partner_bibliography_duplicate_override,
    )
    api.add_route(
        "/api/v1/bibliography/{id_or_citation_key}", partner_bibliography_entry
    )
