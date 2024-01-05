import falcon
from falcon_caching import Cache
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate
import json
from ebl.cache.application.cache import DAILY_TIMEOUT

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
    def __init__(self, bibliography: Bibliography, cache: Cache):
        self._bibliography = bibliography
        self._cache = cache

    def on_get(self, req: Request, resp: Response) -> None:
        ids = req.params["ids"].split(",")
        cache_key = tuple(sorted(set(ids)))

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
