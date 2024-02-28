import json
import falcon
from falcon import Request, Response
from falcon_caching import Cache
from pydash import flow
from ebl.cache.application.cache import DEFAULT_TIMEOUT

from ebl.common.query.parameter_parser import (
    parse_integer_field,
    parse_lines,
    parse_transliteration,
    parse_lemmas,
    parse_pages,
    parse_genre,
)
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.errors import DataError
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.users.web.require_scope import require_fragment_read_scope


class FragmentsRetrieveAllResource:
    def __init__(
        self, repository: FragmentRepository, photos_repository: FileRepository
    ):
        self._repo = repository
        self._photos = photos_repository

    def _parse_skip(self, skip: str, total_count: int) -> int:
        try:
            skip_int = int(skip)
        except ValueError as error:
            raise DataError(f"Skip '{skip}' is not numeric.") from error
        if skip_int < 0:
            raise DataError(f"Skip '{skip}' is negative.")
        if skip_int > total_count:
            raise DataError(
                f"Skip '{skip}' is greater than total count '{total_count}'."
            )
        return skip_int

    def on_get(self, req: Request, resp: Response):
        total_count = self._repo.count_transliterated_fragments(only_authorized=True)
        skip = self._parse_skip(
            req.params.get("skip", 0),
            total_count,
        )
        fragments = self._repo.retrieve_transliterated_fragments(skip)
        fragments_ = []
        # to improve performance we don't serialize the complete Fragment in fragment_repository
        # because we would have to deserialize it again here to return it to client
        for fragment in fragments:
            fragment["atf"] = TextSchema().load(fragment["text"]).atf
            dict.pop(fragment, "text")
            number = MuseumNumberSchema().load(fragment["museumNumber"])
            fragment["hasPhoto"] = self._photos.query_if_file_exists(f"{number}.jpg")
            fragments_.append(fragment)
        resp.media = {"totalCount": total_count, "fragments": fragments_}


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


def make_latest_additions_resource(repository: FragmentRepository, cache: Cache):
    class LatestAdditionsResource:
        def __init__(
            self,
            repository: FragmentRepository,
        ):
            self._repository = repository

        @cache.cached(timeout=DEFAULT_TIMEOUT)
        def on_get(self, req: Request, resp: Response):
            resp.text = json.dumps(
                QueryResultSchema().dump(
                    self._repository.query_latest(
                        req.context.user.get_scopes(
                            prefix="read:", suffix="-fragments"
                        ),
                    )
                )
            )

    return LatestAdditionsResource(repository)


class AllFragmentSignsResource:
    def __init__(
        self,
        repository: FragmentRepository,
    ):
        self._repository = repository

    def on_get(self, req: Request, resp: Response):
        resp.media = self._repository.fetch_fragment_signs()
