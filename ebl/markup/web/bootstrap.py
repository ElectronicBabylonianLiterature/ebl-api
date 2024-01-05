import falcon
from falcon import Request, Response
from falcon_caching import Cache
import json

from ebl.context import Context
from ebl.markup.domain.converters import markup_string_to_json
from ebl.cache.application.cache import DAILY_TIMEOUT


class Markup:
    auth = {"auth_disabled": True}

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = markup_string_to_json(req.params["text"])


class CachedMarkup(Markup):
    def __init__(self, cache: Cache):
        self._cache = cache

    def on_get(self, req: Request, resp: Response) -> None:
        cache_key = hash(req.params["text"])

        if cached := self._cache.get(cache_key):
            resp.text = cached
        else:
            data = json.dumps(markup_string_to_json(req.params["text"]))
            self._cache.set(cache_key, data, timeout=DAILY_TIMEOUT)
            resp.text = data


def create_markup_routes(api: falcon.App, context: Context) -> None:
    api.add_route("/markup", Markup())
    api.add_route("/cached-markup", CachedMarkup(context.cache))
