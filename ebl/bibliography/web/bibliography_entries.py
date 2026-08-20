import falcon
from falcon_caching import Cache
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate
import json
from typing import Mapping, Sequence
from ebl.cache.application.cache import DAILY_TIMEOUT

from ebl.bibliography.application.server_owned_fields import (
    reject_submitted_server_owned_fields,
)
from ebl.bibliography.domain.bibliography_entry import (
    DUPLICATE_CANDIDATE_JSON_SCHEMA,
    PARTNER_CSL_JSON_SCHEMA,
    PARTNER_DUPLICATE_OVERRIDE_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)
from ebl.bibliography.domain.bibliography_requests import (
    INTERNAL_CREATE_JSON_SCHEMA,
    INTERNAL_METADATA_UPDATE_JSON_SCHEMA,
)
from ebl.errors import DataError
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.duplicate_override import DuplicateOverrideError


def submitted_server_owned_fields(
    candidate_entries: Sequence[Mapping[str, object]],
) -> list[str]:
    return sorted(
        {
            field
            for entry in candidate_entries
            for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
            if field in entry
        }
    )


def reject_server_owned_internal_fields(req, _resp, _resource, _params) -> None:
    """Refuse identity state on ordinary internal creation.

    Runs ahead of `@validate` so the caller is told which fields are
    server-owned and where identity is managed, rather than getting the
    schema's generic `additionalProperties` rejection.
    """
    media = req.media
    if isinstance(media, dict):
        reject_submitted_server_owned_fields(media)


def reject_server_owned_partner_fields(req, _resp, _resource, _params) -> None:
    media = req.media
    if not isinstance(media, dict):
        return

    candidate_entries = [media]
    if isinstance(media.get("bibliographyEntry"), dict):
        candidate_entries.append(media["bibliographyEntry"])

    if forbidden_fields := submitted_server_owned_fields(candidate_entries):
        raise DataError(
            "Partner bibliography payload may not include server-owned fields: "
            f"{', '.join(forbidden_fields)}."
        )


class BibliographyResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.search(req.params["query"])

    @falcon.before(require_scope, "write:bibliography")
    @falcon.before(reject_server_owned_internal_fields)
    @validate(INTERNAL_CREATE_JSON_SCHEMA)
    def on_post(self, req: UserRequest, resp: Response) -> None:
        bibliography_entry = req.media
        self._bibliography.create_metadata(bibliography_entry, req.context.user)
        resp.status = falcon.HTTP_CREATED
        resp.location = f"/bibliography/{bibliography_entry['id']}"
        resp.media = bibliography_entry


class BibliographyEntriesResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, _req, resp: Response, id_: str) -> None:
        resp.media = self._bibliography.find(id_)

    @falcon.before(require_scope, "write:bibliography")
    @validate(INTERNAL_METADATA_UPDATE_JSON_SCHEMA)
    def on_post(self, req: UserRequest, resp: Response, id_: str) -> None:
        entry = {**req.media, "id": id_}
        self._bibliography.update_metadata(entry, req.context.user)
        resp.status = falcon.HTTP_NO_CONTENT


class BibliographyList:
    def __init__(self, bibliography: Bibliography, cache: Cache):
        self._bibliography = bibliography
        self._cache = cache

    def on_get(self, req: Request, resp: Response) -> None:
        ids = req.params["ids"].split(",")
        cache_key = ",".join(sorted(set(ids)))

        if cached := self._cache.get(cache_key):
            resp.text = cached
        else:
            data = json.dumps(self._bibliography.find_many(ids))
            self._cache.set(cache_key, data, timeout=DAILY_TIMEOUT)
            resp.text = data


class BibliographyAll:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.list_all_bibliography()


class BibliographyDuplicateCandidatesResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "check:bibliography_duplicates")
    @validate(DUPLICATE_CANDIDATE_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response) -> None:
        limit = min(req.get_param_as_int("limit") or 10, 25)
        resp.media = self._bibliography.find_duplicate_candidates(req.media, limit)


class PartnerBibliographyResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "export:bibliography")
    def on_get(self, req: Request, resp: Response) -> None:
        limit = min(req.get_param_as_int("limit") or 50, 100)
        resp.media = self._bibliography.export_page(req.get_param("cursor"), limit)

    @falcon.before(require_scope, "write:bibliography")
    @falcon.before(reject_server_owned_partner_fields)
    @validate(PARTNER_CSL_JSON_SCHEMA)
    def on_post(self, req: UserRequest, resp: Response) -> None:
        bibliography_entry = req.media
        if duplicate_result := self._bibliography.create_partner_entry(
            bibliography_entry, req.context.user
        ):
            resp.status = falcon.HTTP_CONFLICT
            resp.media = duplicate_result
            return
        resp.status = falcon.HTTP_CREATED
        resp.location = f"/api/v1/bibliography/{bibliography_entry['id']}"
        resp.media = bibliography_entry


class PartnerBibliographyEntryResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "export:bibliography")
    def on_get(self, _req: Request, resp: Response, id_or_citation_key: str) -> None:
        resp.media = self._bibliography.find_partner_entry(id_or_citation_key)

    @falcon.before(require_scope, "write:bibliography")
    @falcon.before(reject_server_owned_partner_fields)
    @validate(PARTNER_CSL_JSON_SCHEMA)
    def on_post(
        self, req: UserRequest, resp: Response, id_or_citation_key: str
    ) -> None:
        if duplicate_result := self._bibliography.update_partner_entry(
            id_or_citation_key, req.media, req.context.user
        ):
            resp.status = falcon.HTTP_CONFLICT
            resp.media = duplicate_result
            return
        resp.status = falcon.HTTP_NO_CONTENT


class PartnerBibliographyResolveResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "export:bibliography")
    def on_get(self, req: Request, resp: Response) -> None:
        identifier = req.get_param("identifier")
        if identifier is None:
            raise falcon.HTTPBadRequest(
                title="Missing identifier",
                description="Query parameter 'identifier' is required.",
            )
        resp.media = self._bibliography.find_partner_entry(identifier)


class PartnerBibliographyDuplicateOverrideResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "write:bibliography")
    @falcon.before(reject_server_owned_partner_fields)
    @validate(PARTNER_DUPLICATE_OVERRIDE_JSON_SCHEMA)
    def on_post(self, req: UserRequest, resp: Response) -> None:
        bibliography_entry = req.media["bibliographyEntry"]
        override = req.media["override"]

        try:
            self._bibliography.create_partner_entry_with_duplicate_override(
                bibliography_entry, override, req.context.user
            )
        except DuplicateOverrideError as error:
            raise falcon.HTTPBadRequest(
                title="Invalid duplicate override", description=str(error)
            ) from error

        resp.status = falcon.HTTP_CREATED
        resp.location = f"/api/v1/bibliography/{bibliography_entry['id']}"
        resp.media = bibliography_entry
