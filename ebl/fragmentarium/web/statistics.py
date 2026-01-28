import json

import falcon
from falcon_caching import Cache
from falcon_caching.utils import register

from ebl.cache.application.cache import DEFAULT_TIMEOUT, cache_control
from ebl.fragmentarium.application.fragmentarium import Fragmentarium


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
