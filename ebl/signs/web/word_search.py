import falcon

from ebl.transliteration.infrastructure.mongo_sign_repository import SignSchema
from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
        self.signs = signs

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        x = SignSchema().dump(self.signs.query(req.params["query"]), many=True)
        print(x)
        resp.media = x
