import falcon
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.domain.bibliography_entry import CSL_JSON_SCHEMA
from ebl.users.web.require_scope import require_scope
from ebl.bibliography.application.bibliography import Bibliography


class BibliographyResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.search(req.params["query"])

    @falcon.before(require_scope, "write:bibliography")
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response) -> None:
        bibliography_entry = req.media
        self._bibliography.create(bibliography_entry, req.context.user)
        resp.status = falcon.HTTP_CREATED
        resp.location = f'/bibliography/{bibliography_entry["id"]}'
        resp.media = bibliography_entry


class BibliographyEntriesResource:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, _req, resp: Response, id_: str) -> None:
        resp.media = self._bibliography.find(id_)

    @falcon.before(require_scope, "write:bibliography")
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req: Request, resp: Response, id_: str) -> None:
        entry = {**req.media, "id": id_}
        self._bibliography.update(entry, req.context.user)
        resp.status = falcon.HTTP_NO_CONTENT


class BibliographyList:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.list_all_bibliography()


class IndexedBibliographyList:
    def __init__(self, bibliography: Bibliography):
        self._bibliography = bibliography

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._bibliography.list_all_indexed_bibliography()
