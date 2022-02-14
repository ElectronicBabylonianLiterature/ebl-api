import falcon
from falcon_caching import Cache

from ebl.fragmentarium.application.fragmentarium import Fragmentarium


def make_statistics_resource(cache: Cache, fragmentarium: Fragmentarium):
    class StatisticsResource:
        auth = {"auth_disabled": True}

        def __init__(self, fragmentarium: Fragmentarium):
            self._fragmentarium = fragmentarium

        @cache.cached(timeout=600)
        def on_get(self, _req, resp: falcon.Response) -> None:
            resp.media = self._fragmentarium.statistics()
            resp.cache_control = ["public", "max-age=600"]

    return StatisticsResource(fragmentarium)
