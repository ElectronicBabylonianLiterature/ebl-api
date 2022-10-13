import falcon
from falcon import Request, Response
from typing import Sequence

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.domain.fragment import Scope


def check_fragment_scope(user: User, scopes: Sequence[Scope]):
    for scope_class in scopes:
        scope = f"read:{scope_class}-fragments"
        if not user.has_scope(scope):
            raise falcon.HTTPForbidden()


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: Request, resp: Response, number: str):
        user: User = req.context.user
        fragment, has_photo = self._finder.find(parse_museum_number(number))
        if fragment.scopes:
            check_fragment_scope(req.context.user, fragment.scopes)
        resp.media = create_response_dto(fragment, user, has_photo)
