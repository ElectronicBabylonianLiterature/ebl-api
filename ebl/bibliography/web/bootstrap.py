from datetime import datetime, timezone

import falcon

from ebl.bibliography.web.bibliography_entries import (
    BibliographyEntriesResource,
    BibliographyResource,
    BibliographyAll,
    BibliographyDuplicateCandidatesResource,
    BibliographyList,
    PartnerBibliographyDuplicateOverrideResource,
    PartnerBibliographyEntryResource,
    PartnerBibliographyResolveResource,
    PartnerBibliographyResource,
)
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.bibliography.web.bibliography_identity_management import (
    BibliographyIdentityResource,
)
from ebl.context import Context


def create_bibliography_routes(api: falcon.App, context: Context):
    context.bibliography_repository.create_indexes()
    context.bibliography_repository.reconcile_lookup_reservations(
        datetime.now(timezone.utc)
    )
    bibliography = context.get_bibliography()
    bibliography_resource = BibliographyResource(bibliography)
    bibliography_entries = BibliographyEntriesResource(bibliography)
    bibliography_all = BibliographyAll(bibliography)
    bibliography_list = BibliographyList(bibliography, context.cache)
    duplicate_candidates = BibliographyDuplicateCandidatesResource(bibliography)
    bibliography_identity = BibliographyIdentityResource(
        BibliographyIdentityManagement(
            context.bibliography_repository, context.changelog, bibliography.find
        )
    )
    partner_bibliography = PartnerBibliographyResource(bibliography)
    partner_bibliography_duplicate_override = (
        PartnerBibliographyDuplicateOverrideResource(bibliography)
    )
    partner_bibliography_entry = PartnerBibliographyEntryResource(bibliography)
    partner_bibliography_resolve = PartnerBibliographyResolveResource(bibliography)

    api.add_route("/bibliography", bibliography_resource)
    api.add_route("/bibliography/all", bibliography_all)
    api.add_route("/bibliography/list", bibliography_list)
    api.add_route("/bibliography/{id_}", bibliography_entries)
    api.add_route("/bibliography/{id_}/identity", bibliography_identity)
    api.add_route("/api/v1/bibliography/duplicate-candidates", duplicate_candidates)
    api.add_route("/api/v1/bibliography", partner_bibliography)
    api.add_route(
        "/api/v1/bibliography/duplicate-override",
        partner_bibliography_duplicate_override,
    )
    api.add_route("/api/v1/bibliography/resolve", partner_bibliography_resolve)
    api.add_route(
        "/api/v1/bibliography/{id_or_citation_key}", partner_bibliography_entry
    )
