import re
from typing import Sequence

import falcon  # pyre-ignore
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate
from pydash import uniq_with  # pyre-ignore

from ebl.bibliography.domain.bibliography_entry import CSL_JSON_SCHEMA
from ebl.users.web.require_scope import require_scope


class BibliographyResource:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "read:bibliography")
    def on_get(self, req: Request, resp: Response) -> None:  # pyre-ignore[11]
        resp.media = self._parse_search_request(req.params)

    def _author_and_title_query(self, query: str) -> Sequence[dict]:
        match = re.match(r'^([^\d]+)(?: (\d{4})(?: (.*))?)?$', query)
        if match:
            return self._bibliography.search_author_year_and_title(
                match.group(1),
                int(match.group(2)) if match.group(2) else None,
                match.group(3)
            )
        else:
            return []

    def _collection_title_short_and_collection_number(self, query: str)\
            -> Sequence[dict]:
        match = re.match(r'^([^\s]+)(?: (\d*))?$', query)
        if match:
            return self._bibliography.search_container_title_and_collection_number(
                match.group(1),
                int(match.group(2)) if match.group(2) else None,
            )
        else:
            return []

    def _parse_search_request(self, req_params,) -> Sequence[dict]:
        first_query = self._author_and_title_query(req_params.get("query"))
        second_query = self._collection_title_short_and_collection_number(
            req_params.get("query"))
        queries_combined = uniq_with(first_query + second_query, lambda a, b: a == b)
        return queries_combined

    @falcon.before(require_scope, "write:bibliography")
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response) -> None:  # pyre-ignore[11]
        bibliography_entry = req.media
        self._bibliography.create(bibliography_entry, req.context.user)
        resp.status = falcon.HTTP_CREATED
        resp.location = f'/bibliography/{bibliography_entry["id"]}'
        resp.media = bibliography_entry


class BibliographyEntriesResource:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "read:bibliography")
    def on_get(self, _req, resp: Response, id_: str) -> None:  # pyre-ignore[11]
        resp.media = self._bibliography.find(id_)

    @falcon.before(require_scope, "write:bibliography")
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response, id_: str) -> None:  # pyre-ignore[11]
        entry = {**req.media, "id": id_}
        self._bibliography.update(entry, req.context.user)
        resp.status = falcon.HTTP_NO_CONTENT
