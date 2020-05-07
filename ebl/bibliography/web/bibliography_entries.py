from typing import Optional, Tuple

import falcon  # pyre-ignore
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.domain.bibliography_entry import CSL_JSON_SCHEMA
from ebl.errors import DataError
from ebl.users.web.require_scope import require_scope


class BibliographyResource:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, "read:bibliography")
    def on_get(self, req: Request, resp: Response) -> None:  # pyre-ignore[11]
        resp.media = self._bibliography.search([*self._parse_search_request(req)])

    @staticmethod
    def _parse_number(number: str) -> Optional[int]:
        return None if number == "" else int(number)

    @staticmethod
    def _parse_search_request(
        req,
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        first = "0"
        second = "1"
        third = "2"
        allowed_params = {first, second, third}
        req_params = set(req.params.keys())
        if not req_params <= allowed_params:
            extra_params = req_params - allowed_params
            raise DataError(f"Unsupported query parameters: {extra_params}.")
        try:
            return (
                req.params.get(first),
                (
                    BibliographyResource._parse_number(req.params[second])
                    if second in req.params
                    else None
                ),
                req.params.get(third),
            )
        except ValueError:
            raise DataError(f'"{second}" is not numeric.')

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
