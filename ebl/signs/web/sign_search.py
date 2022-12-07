from typing import Dict

import falcon

from ebl.dispatcher import create_dispatcher
from ebl.errors import DataError
from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.users.web.require_scope import require_scope
from ebl.signs.web.logograms_injector import inject_logograms_unicode


class SignsSearch:
    def __init__(self, signs: SignRepository):
        self.sign_repository = signs
        self._dispatch = create_dispatcher(
            {
                frozenset(
                    ["listsName", "listsNumber"]
                ): lambda params: signs.search_by_lists_name(
                    params["listsName"], params["listsNumber"]
                ),
                frozenset(["value", "subIndex"]): lambda params: signs.search_all(
                    params["value"], params["subIndex"]
                ),
                frozenset(
                    ["value", "isIncludeHomophones", "subIndex"]
                ): lambda params: signs.search_include_homophones(params["value"]),
                frozenset(
                    ["value", "subIndex", "isComposite"]
                ): lambda params: signs.search_composite_signs(
                    params["value"], params["subIndex"]
                ),
                frozenset(["wordId"]): lambda params: signs.search_by_lemma(
                    params["wordId"]
                ),
            }
        )

    @staticmethod
    def _parse_sub_index(params: Dict) -> Dict:
        params_copy = params.copy()
        if "subIndex" in params_copy.keys():
            try:
                params_copy["subIndex"] = int(params_copy["subIndex"])
            except ValueError:
                raise DataError(
                    f"""subIndex '{params_copy["subIndex"]}' has to be a number"""
                )
        return params_copy

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        signs = self._dispatch(self._parse_sub_index(req.params))
        if "wordId" in req.params:
            signs = inject_logograms_unicode(
                signs, req.params["wordId"], self.sign_repository
            )
        resp.media = SignDtoSchema().dump(signs, many=True)
