import json
import falcon


class TranslitarationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    def on_post(self, req, resp, number):
        try:
            transliteration = json.loads(req.stream.read())
            self._fragmentarium.update_transliteration(number, transliteration)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
