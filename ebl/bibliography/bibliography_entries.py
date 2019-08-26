from typing import Optional, Tuple

import falcon
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.bibliography_entry import CSL_JSON_SCHEMA
from ebl.errors import DataError
from ebl.require_scope import require_scope


class BibliographyResource:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, 'read:bibliography')
    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.search(
            *self._parse_search_request(req)
        )

    @staticmethod
    def _parse_year(year: str) -> Optional[int]:
        return None if year == '' else int(year)

    @staticmethod
    def _parse_search_request(req) -> Tuple[Optional[str],
                                            Optional[int],
                                            Optional[str]]:
        author = 'author'
        year = 'year'
        title = 'title'
        allowed_params = {author, year, title}
        req_params = set(req.params.keys())
        if not req_params <= allowed_params:
            extra_params = req_params - allowed_params
            raise DataError(f'Unsupported query parameters: {extra_params}.')
        try:
            return (
                req.params.get(author),
                (BibliographyResource._parse_year(req.params[year])
                 if year in req.params
                 else None),
                req.params.get(title)
            )
        except ValueError:
            raise DataError(f'Year "{year}" is not numeric.')

    @falcon.before(require_scope, 'write:bibliography')
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response) -> None:
        bibliography_entry = req.media
        self._bibliography.create(bibliography_entry, req.context['user'])
        resp.status = falcon.HTTP_CREATED
        resp.location = f'/bibliography/{bibliography_entry["id"]}'
        resp.media = bibliography_entry


class BibliographyEntriesResource:

    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, 'read:bibliography')
    def on_get(self, _req,  resp: Response, id_: str) -> None:
        resp.media = self._bibliography.find(id_)

    @falcon.before(require_scope, 'write:bibliography')
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response, id_: str) -> None:
        entry = {**req.media, 'id': id_}
        self._bibliography.update(entry, req.context['user'])
        resp.status = falcon.HTTP_NO_CONTENT
