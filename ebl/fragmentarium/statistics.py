class StatisticsResource:

    auth = {
        'auth_disabled': True
    }

    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    def on_get(self, _req, resp):
        resp.media = self._fragmentarium.statistics()
