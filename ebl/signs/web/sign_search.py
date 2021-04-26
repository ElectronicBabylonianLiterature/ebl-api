from typing import Dict

import falcon

from ebl.dispatcher import create_dispatcher
from ebl.errors import DataError
from ebl.transliteration.infrastructure.mongo_sign_repository import SignSchema
from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
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
            }
        )

    @staticmethod
    def _parse_params(params):
        if "subIndex" in params.keys():
            try:
                params["subIndex"] = int(params["subIndex"])
            except ValueError:
                raise DataError(
                    f"""subIndex '{params["subIndex"]}' has to be a number"""
                )
        return params

    @staticmethod
    def _replace_id(sign) -> Dict:
        sign["name"] = sign.pop("_id")
        return sign

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        try:
            resp.media = list(
                map(
                    self._replace_id,
                    SignSchema().dump(
                        self._dispatch(self._parse_params(req.params)), many=True
                    ),
                )
            )
        except Exception as e:
            print(e)
