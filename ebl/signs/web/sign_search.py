from typing import Dict

import falcon

from ebl.transliteration.infrastructure.mongo_sign_repository import SignSchema
from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
        self.signs = signs

    @staticmethod
    def replace_id(sign) -> Dict:
        sign["name"] = sign.pop("_id")
        return sign

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        sign_query = req.params
        if sign_query["isIncludeHomophones"] == "true":
            sign_dumped = SignSchema().dump(self.signs.search_include_homophones(sign_query["value"]), many=True)
        elif sign_query["isComposite"] == "true":
            sign_dumped = SignSchema().dump(
                self.signs.search_composite_signs(sign_query["value"], sign_query.get("subIndex", None), many=True)
            )
        else:
            sign_dumped = SignSchema().dump(
                self.signs.search_all(
                    sign_query["value"], sign_query.get("subIndex", None)
                ), many=True
            )

        resp.media = list(map(self.replace_id, sign_dumped))
