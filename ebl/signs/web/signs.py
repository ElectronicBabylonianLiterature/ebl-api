import falcon

from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.users.web.require_scope import require_scope


class SignsResource:
    def __init__(self, signs: SignRepository):
        self._signs = signs

    @falcon.before(require_scope, "read:words")
    def on_get(self, _req, resp, object_id):
        resp.media = SignDtoSchema().dump(self._signs.find(object_id))
