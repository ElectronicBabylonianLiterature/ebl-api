import falcon
from falcon import Request, Response
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.common.query.parameter_parser import (
    parse_integer_field,
    parse_lines,
    parse_transliteration,
    parse_lemmas,
    parse_pages,
)

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_fragment_scope
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from pydash import flow


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_fragment_scope)
    def on_get(self, req: Request, resp: Response, number: str):
        lines = parse_lines(req.get_param_as_list("lines", default=[]))

        fragment, has_photo = self._finder.find(
            parse_museum_number(number),
            lines=lines,
        )
        resp.media = create_response_dto(fragment, req.context.user, has_photo)


class FragmentsQueryResource:
    def __init__(
        self,
        repository: FragmentRepository,
        transliteration_query_factory: TransliterationQueryFactory,
    ):
        self._repository = repository
        self._transliteration_query_factory = transliteration_query_factory

    def on_get(self, req: Request, resp: Response):
        parse = flow(
            parse_transliteration(self._transliteration_query_factory),
            parse_lemmas,
            parse_pages,
            parse_integer_field("limit"),
        )

        resp.media = QueryResultSchema().dump(
            self._repository.query(
                parse(req.params),
                req.context.user.get_scopes(prefix="read:", suffix="-fragments"),
            )
        )
