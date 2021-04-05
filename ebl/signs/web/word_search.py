import falcon

from ebl.users.web.require_scope import require_scope


class SignsSearch:
    def __init__(self, signs):
        self.signs = signs

    @falcon.before(require_scope, "read:words")
    def on_get(self, req, resp):
        print(req.params)
        resp.media = self.signs.find(req.params["query"])
