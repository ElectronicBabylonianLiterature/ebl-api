import falcon
from falcon import Request, Response
from typing import Sequence

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


def check_fragment_scope(user: User, scopes: Sequence[str]):
    for scope_class in scopes:
        scope = f"read:{scope_class}-fragments"
        if not user.has_scope(scope):
            raise falcon.HTTPForbidden()


SCOPES = ["caic", "sipparlibrary", "uruklbu"]


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(
        self, req: Request, resp: Response, number: str
    ):
        scopes: Sequence[str] = []  # ToDo: retrieve scope from Fragment
        if scopes:
            check_fragment_scope(req.context.user, scopes)
        user: User = req.context.user
        fragment, has_photo = self._finder.find(parse_museum_number(number))
        resp.media = create_response_dto(fragment, user, has_photo)
