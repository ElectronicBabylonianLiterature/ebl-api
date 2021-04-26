from typing import Dict, Union

import falcon

from ebl.dispatcher import create_dispatcher
from ebl.transliteration.infrastructure.mongo_sign_repository import SignSchema
from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
        self._dispatch = create_dispatcher(
            {
                frozenset(["listsName", "listsNumber"]): lambda params: signs.search_by_lists_name(params["value"], params["subIndex"]),
                frozenset(["value", "subIndex", "isComposite"]): lambda params: signs.search_composite_signs(params["value"], params["subIndex"]),
                frozenset(["value", "includeHomophones"]): lambda params: signs.search_include_homophones(params["value"]),
                frozenset(["value", "subIndex", "isComposite"]): lambda params: signs.search_include_homophones(params["value"], params["subIndex"])
            }
        )

    @staticmethod
    def _parse_params(params: Dict[str]) -> Dict:
        if "subIndex" in params.keys():
            params["subIndex"] = int(params["subIndex"])
            return params

    @staticmethod
    def _replace_id(sign) -> Dict:
        sign["name"] = sign.pop("_id")
        return sign

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        sign_dumped = SignSchema().load(self._dispatch(self._parse_params(req.params)), many=True)
        resp.media = list(map(self._replace_id, sign_dumped))
