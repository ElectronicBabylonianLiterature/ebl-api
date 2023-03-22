from typing import Tuple
import falcon
from ebl.lemmatization.application.suggestion_finder import SuggestionFinder


def get_parameters(params: dict) -> Tuple[str, bool]:
    try:
        word = params["word"]
        is_normalized = (
            {"true": True, "false": False}[params["isNormalized"]]
            if "isNormalized" in params
            else False
        )
        return (word, is_normalized)
    except KeyError as error:
        raise falcon.HTTPUnprocessableEntity(
            description=(
                f"Invalid value {params.get('isNormalized')} for isNormalized. "
                "Expected true or false."
            )
        ) from error


class LemmaSearch:
    def __init__(self, finder: SuggestionFinder):
        self._finder = finder

    def on_get(self, req, resp):
        allowed_params = {"word", "isNormalized"}
        if not set(req.params.keys()).issubset(allowed_params):
            raise falcon.HTTPUnprocessableEntity()

        resp.media = self._finder.find_lemmas(*get_parameters(req.params))
