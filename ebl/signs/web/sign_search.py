import falcon

from ebl.transliteration.infrastructure.mongo_sign_repository import SignSchema
from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
        self.signs = signs

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        sign_query = req.params
        if sign_query["isIncludeHomophones"] == "true":
            resp.media = SignSchema().dump(self.signs.search_all(sign_query["value"]))
        elif sign_query["isComposite"] == "true":
            resp.media = SignSchema().dump(self.signs.search_composite_signs(sign_query["value"]))
        else:
            resp.media = SignSchema().dump(self.signs.search_all(sign_query["value"], sign_query["subIndex"] if sign_query["subIndex"] != "" else None))

