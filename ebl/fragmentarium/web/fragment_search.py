from typing import Tuple

import falcon
from falcon_caching import Cache

from ebl.cache.application.cache import DEFAULT_TIMEOUT, cache_control
from ebl.dispatcher import create_dispatcher
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_info_schema import (
    ApiFragmentInfoSchema,
)
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.users.web.require_scope import require_fragment_scope

CACHED_COMMANDS = frozenset({"latest", "needsRevision"})


class FragmentSearch:
    def __init__(
        self,
        fragmentarium: Fragmentarium,
        finder: FragmentFinder,
        transliteration_query_factory: TransliterationQueryFactory,
        cache: Cache,
    ):
        @cache.memoize(DEFAULT_TIMEOUT)
        def find_needs_revision(_):
            return fragmentarium.find_needs_revision()

        @cache.memoize(DEFAULT_TIMEOUT)
        def find_latest(_):
            return fragmentarium.find_latest()

        self.api_fragment_info_schema = ApiFragmentInfoSchema(many=True)
        self._transliteration_query_factory = transliteration_query_factory
        self._dispatch = create_dispatcher(
            {
                frozenset(["random"]): lambda _: self.api_fragment_info_schema.dump(
                    finder.find_random()
                ),
                frozenset(
                    ["interesting"]
                ): lambda _: self.api_fragment_info_schema.dump(
                    finder.find_interesting()
                ),
                frozenset(["latest"]): lambda x: self.api_fragment_info_schema.dump(
                    find_latest(x)
                ),
                frozenset(
                    ["needsRevision"]
                ): lambda x: self.api_fragment_info_schema.dump(find_needs_revision(x)),
            }
        )

    @staticmethod
    def _validate_pagination_index(paginationIndex: str) -> int:
        try:
            int(paginationIndex)
        except ValueError as error:
            raise DataError(
                f'Pagination Index "{paginationIndex}" is not numeric.'
            ) from error
        return int(paginationIndex)

    @staticmethod
    def _validate_pages(id: str, pages: str) -> Tuple[str, str]:
        if pages:
            if not id:
                raise DataError("Name, Year or Title required")
            try:
                int(pages)
            except ValueError as error:
                raise DataError(f'Pages "{pages}" not numeric.') from error
        return id, pages

    @falcon.before(require_fragment_scope)
    @cache_control(
        ["private", "max-age=600"],
        when=lambda req, _: req.params.keys() <= CACHED_COMMANDS,
    )
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._dispatch(req.params)
