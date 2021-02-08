import falcon  # pyre-ignore

from ebl.fragmentarium.application.fragmentarium import Fragmentarium


class StatisticsResource:

    auth = {"auth_disabled": True}

    def __init__(self, fragmentarium: Fragmentarium):
        self._fragmentarium = fragmentarium

    def on_get(self, _req, resp: falcon.Response) -> None:  # pyre-ignore[11]
        resp.media = self._fragmentarium.statistics()
        resp.cache_control = ["public", "max-age=600"]
