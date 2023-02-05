import falcon
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.domain.folios import Folio
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


def check_folio_scope(user: User, name: str):
    scope = f"read:{name}-folios"
    if not user.has_scope(scope):
        raise falcon.HTTPForbidden()


class FoliosResource:

    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: Request, resp: Response, name: str, number: str):
        check_folio_scope(req.context.user, name)
        file = self._finder.find_folio(Folio(name, number))

        resp.content_type = file.content_type
        resp.content_length = file.length
        resp.stream = file
