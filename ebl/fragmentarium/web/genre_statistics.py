import json
import falcon
from falcon_caching import Cache
from falcon_caching.utils import register

from ebl.cache.application.cache import DEFAULT_TIMEOUT, cache_control
from ebl.fragmentarium.application.fragmentarium import Fragmentarium


def make_genre_statistics_resource(cache: Cache, fragmentarium: Fragmentarium):
    class GenreStatisticsResource:
        auth = {"auth_disabled": True}

        def __init__(self, fragmentarium: Fragmentarium):
            self._fragmentarium = fragmentarium

        @register(
            cache_control(["public", f"max-age={DEFAULT_TIMEOUT}"]),
            cache.cached(timeout=DEFAULT_TIMEOUT),
        )
        def on_get(self, _req, resp: falcon.Response) -> None:
            genre_counts = self._fragmentarium.genre_statistics()
            resp.text = json.dumps({
                str(list(k)): v for k, v in genre_counts.items()
            })

    return GenreStatisticsResource(fragmentarium)
