import re

import falcon  # pyre-ignore
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate


from ebl.bibliography.domain.bibliography_entry import CSL_JSON_SCHEMA
from ebl.users.web.require_scope import require_scope


class BibliographyResource:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "read:bibliography")
    def on_get(self, req: Request, resp: Response) -> None:  # pyre-ignore[11]
        parsed_request = self._parse_search_request(req.params["query"])
        resp.media = self._bibliography.search(parsed_request)

    @staticmethod
    def _parse_search_request(request) -> dict:
        parsed_request = {
            "query_1": dict.fromkeys(["author", "year", "title"]),
            "query_2": dict.fromkeys(["container_title_short", "collection_number"])
        }
        match = re.match(r'^([^\d]+)(?: (\d{1,4})(?: (.*))?)?$', request)
        if match:
            parsed_request["query_1"]["author"] = match.group(1)
            parsed_request["query_1"]["year"] = int(match.group(2))\
                if match.group(2) else None
            parsed_request["query_1"]["title"] = match.group(3)

        match = re.match(r'^([^\s]+)(?: (\d*))?$', request)
        if match:
            parsed_request["query_2"]["container_title_short"] = match.group(1)
            parsed_request["query_2"]["collection_number"] = match.group(2)
        return parsed_request

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
