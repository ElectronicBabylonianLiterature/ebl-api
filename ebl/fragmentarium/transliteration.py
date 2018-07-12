import json
import falcon

EBL_NAME = 'https://ebabylon.org/eblName'


class TranslitarationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium, fetch_user_profile):
        self._fragmentarium = fragmentarium
        self._fetch_user_profile = fetch_user_profile

    def on_post(self, req, resp, number):
        user = self._fetch_user_profile(req)
        print(user, flush=True)
        try:
            transliteration = json.loads(req.stream.read())
            self._fragmentarium.update_transliteration(
                number,
                transliteration,
                user[EBL_NAME] or user['name']
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
