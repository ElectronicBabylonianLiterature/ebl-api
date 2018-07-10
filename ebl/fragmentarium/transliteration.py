import json
import falcon


class TranslitarationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium, fetch_user_profile):
        self._fragmentarium = fragmentarium
        self._fetch_user_profile = fetch_user_profile

    def on_post(self, req, resp, number):
        user = self._fetch_user_profile(req)['name']

        try:
            transliteration = json.loads(req.stream.read())
            self._fragmentarium.update_transliteration(
                number,
                transliteration,
                user
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
