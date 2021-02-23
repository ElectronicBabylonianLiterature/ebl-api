from typing import Tuple

import falcon

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.users.web.require_scope import require_scope


def get_parameters(params: dict) -> Tuple[str, bool]:
    try:
        word = params["word"]
        is_normalized = (
            {"true": True, "false": False}[params["isNormalized"]]
            if "isNormalized" in params
            else False
        )
        return (word, is_normalized)
    except KeyError:
        raise falcon.HTTPUnprocessableEntity()


class LemmaSearch:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        allowed_params = {"word", "isNormalized"}
        if not set(req.params.keys()).issubset(allowed_params):
            raise falcon.HTTPUnprocessableEntity()

        resp.media = self._finder.find_lemmas(*get_parameters(req.params))
