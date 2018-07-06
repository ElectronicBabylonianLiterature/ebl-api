import falcon


class FragmentsResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    def on_get(self, _req, resp, number):
        try:
            resp.media = self._fragmentarium.find(number)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
