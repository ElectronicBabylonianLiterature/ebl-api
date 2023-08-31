from typing import cast

import falcon
from falcon import Request, Response
from marshmallow import fields

from ebl.common.query.query_schemas import QueryResultSchema
from ebl.common.query.parameter_parser import (
    parse_integer_field,
    parse_lines,
    parse_transliteration,
    parse_lemmas,
    parse_pages,
    parse_genre,
)
from ebl.errors import DataError

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import RETRIEVE_ALL_LIMIT
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_fragment_read_scope
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from pydash import flow


class FragmentRetrieveAllDtoSchema(FragmentSchema):
    _id = fields.Function(lambda fragment: str(fragment.number))
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )

    class Meta:
        exclude = (
            "folios",
            "legacy_script",
            "text",
            "authorized_scopes",
            "references",
            "uncurated_references",
            "folios",
            "line_to_vec",
        )


class FragmentsRetrieveAllResource:
    def __init__(self, repository: FragmentRepository, finder: FragmentFinder):
        self._repo = repository
        self.finder = finder

    def _parse_skip(self, skip: str, limit: int, total_count: int) -> int:
        try:
            skip_int = int(skip)
        except ValueError as error:
            raise DataError(f"Skip '{skip}' is not numeric.") from error
        if skip_int < 0:
            raise DataError(f"Skip '{skip}' is negative.")
        if skip_int + limit > total_count:
            raise DataError(
                f"Skip '{skip}' is greater than total count '{total_count}'."
            )
        return skip_int

    def on_get(self, req: Request, resp: Response):
        total_count = self._repo.count_transliterated_fragments_with_authorization()
        skip = self._parse_skip(
            req.params.get("skip", default=0),
            RETRIEVE_ALL_LIMIT,
            total_count,
        )
        fragments = self._repo.retrieve_transliterated_fragments(skip)
        has_photos = []
        for fragment in fragments:
            _, has_photo = self.finder.find(fragment.number)
            has_photos.append(has_photo)
        resp.media = {
            "totalCount": total_count,
            "fragments": [
                FragmentRetrieveAllDtoSchema(context={"has_photo": has_photo}).dump(
                    fragment
                )
                for has_photo, fragment in zip(has_photos, fragments)
            ],
        }


class FragmentsResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    @falcon.before(require_fragment_read_scope)
    def on_get(self, req: Request, resp: Response, number: str):
        lines = parse_lines(req.get_param_as_list("lines", default=[]))
        exclude_lines = req.get_param_as_bool("excludeLines", default=False)

        fragment, has_photo = self._finder.find(
            parse_museum_number(number), lines=lines, exclude_lines=exclude_lines
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
            parse_genre,
            parse_integer_field("limit"),
        )

        resp.media = QueryResultSchema().dump(
            self._repository.query(
                parse(req.params),
                req.context.user.get_scopes(prefix="read:", suffix="-fragments"),
            )
        )


class FragmentsListResource:
    def __init__(
        self,
        repository: FragmentRepository,
    ):
        self._repository = repository

    def on_get(self, req: Request, resp: Response):
        resp.media = self._repository.list_all_fragments()
