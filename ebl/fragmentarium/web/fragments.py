import falcon
from falcon import Request, Response
from typing import Sequence, Optional, List
from ebl.common.query.query_schemas import QueryResultSchema

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import QueryType
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.domain.fragment import Scope
from ebl.errors import DataError


def check_fragment_scope(user: User, scopes: Sequence[Scope]):
    if not user.can_read_fragment([scope_group.value for scope_group in scopes]):
        raise falcon.HTTPForbidden()


def parse_lines(lines: Optional[List[str]]) -> Optional[List[int]]:
    if lines == ["None"]:
        return []
    elif lines is None:
        return None

    try:
        return [int(line) for line in lines]
    except ValueError as error:
        raise DataError("Lines must be a list of integers") from error


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: Request, resp: Response, number: str):
        user: User = req.context.user
        lines = parse_lines(req.get_param_as_list("lines"))

        fragment, has_photo = self._finder.find(
            parse_museum_number(number),
            lines=lines,
        )
        if fragment.authorized_scopes:
            check_fragment_scope(req.context.user, fragment.authorized_scopes)
        resp.media = create_response_dto(fragment, user, has_photo)


class FragmentsQueryResource:
    def __init__(self, repository: FragmentRepository):
        self._repository = repository

    def on_get(self, req: Request, resp: Response):
        cmd, lemmas = next(iter(req.params.items()))
        resp.media = QueryResultSchema().dump(
            self._repository.query_lemmas(QueryType[cmd.upper()], lemmas.split("+"))
        )
