from functools import wraps
import json
from typing import Sequence

import falcon
from falcon_caching import Cache
from falcon_caching.utils import register

from ebl.cache import DEFAULT_TIMEOUT
from ebl.fragmentarium.application.fragmentarium import Fragmentarium


def cache_control(directives: Sequence[str]):
    def decorator(function):
        @wraps(function)
        def wrapper(self, req, resp, *args, **kwargs):
            result = function(self, req, resp, *args, **kwargs)

            resp.cache_control = directives

            return result

        return wrapper

    return decorator


def make_statistics_resource(cache: Cache, fragmentarium: Fragmentarium):
    class StatisticsResource:
        auth = {"auth_disabled": True}

        def __init__(self, fragmentarium: Fragmentarium):
            self._fragmentarium = fragmentarium

        @register(
            cache_control(["public", f"max-age={DEFAULT_TIMEOUT}"]),
            cache.cached(timeout=DEFAULT_TIMEOUT),
        )
        def on_get(self, _req, resp: falcon.Response) -> None:
            # Falcon-Caching 1.0.1 does not cache resp.media.
            resp.text = json.dumps(self._fragmentarium.statistics())

    return StatisticsResource(fragmentarium)
