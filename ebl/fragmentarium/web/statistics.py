import falcon

from ebl.fragmentarium.application.fragmentarium import Fragmentarium


class StatisticsResource:

    auth = {"auth_disabled": True}

    def __init__(self, fragmentarium: Fragmentarium):
        self._fragmentarium = fragmentarium

    def on_get(self, _req, resp: falcon.Response) -> None:
        resp.media = self._fragmentarium.statistics()
        resp.set_header("Cache-Control", "public, max-age=600")
