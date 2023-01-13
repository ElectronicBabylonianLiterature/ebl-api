import falcon
from falcon import Request, Response
from typing import Sequence
from ebl.common.query.query_schemas import QueryResultSchema

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import QueryType
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.domain.fragment import Scope
from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


def check_fragment_scope(user: User, scopes: Sequence[Scope]):
    if not user.can_read_fragment([scope_group.value for scope_group in scopes]):
        raise falcon.HTTPForbidden()


def parse_lines(lines: Sequence[str]) -> Sequence[int]:
    try:
        return [int(line) for line in lines]
    except ValueError as error:
        raise DataError(
            f"lines must be a list of integers, got {lines} instead"
        ) from error


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: Request, resp: Response, number: str):
        user: User = req.context.user
        lines = parse_lines(req.get_param_as_list("lines", default=[]))

        fragment, has_photo = self._finder.find(
            parse_museum_number(number),
            lines=lines,
        )
        if fragment.authorized_scopes:
            check_fragment_scope(req.context.user, fragment.authorized_scopes)
        resp.media = create_response_dto(fragment, user, has_photo)


class FragmentsQueryResource:
    def __init__(
        self,
        repository: FragmentRepository,
        transliteration_query_factory: TransliterationQueryFactory,
    ):
        self._repository = repository
        self._transliteration_query_factory = transliteration_query_factory

    def on_get(self, req: Request, resp: Response):
        parameters = {**req.params}

        if "lemmas" in parameters:
            parameters["lemmas"] = parameters["lemmas"].split("+")
            parameters["lemmaOperator"] = QueryType[
                "AND"
                if len(parameters["lemmas"]) == 1
                else parameters.get("lemmaOperator", "and").upper()
            ]
        if "transliteration" in parameters:
            parameters["transliteration"] = [
                self._transliteration_query_factory.create(line).regexp
                for line in parameters["transliteration"].strip().split("\n")
                if line
            ]
        if "limit" in parameters:
            parameters["limit"] = int(parameters["limit"])

        if "pages" in parameters:
            pages = parameters["pages"]
            if "bibId" not in parameters:
                raise DataError("Name, Year or Title required")
            try:
                parameters["pages"] = int(pages)
            except ValueError as error:
                raise DataError(f'Pages "{pages}" not numeric.') from error

        resp.media = QueryResultSchema().dump(self._repository.query(parameters))
