from typing import Tuple, Sequence

import falcon
from falcon_caching import Cache

from ebl.cache.application.cache import DEFAULT_TIMEOUT, cache_control
from ebl.common.domain.scopes import Scope
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

CACHED_COMMANDS = frozenset({"needsRevision"})


class FragmentSearch:
    def __init__(
        self,
        fragmentarium: Fragmentarium,
        finder: FragmentFinder,
        transliteration_query_factory: TransliterationQueryFactory,
        cache: Cache,
    ):
        @cache.memoize(DEFAULT_TIMEOUT)
        def find_needs_revision(user_scopes: Sequence[Scope] = tuple()):
            return fragmentarium.find_needs_revision(user_scopes)

        self.api_fragment_info_schema = ApiFragmentInfoSchema(many=True)
        self._transliteration_query_factory = transliteration_query_factory
        self._dispatch = create_dispatcher(
            {
                frozenset(["random"]): lambda _: finder.find_random,
                frozenset(["interesting"]): lambda _: finder.find_interesting,
                frozenset(["needsRevision"]): lambda _: find_needs_revision,
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

    @cache_control(
        ["private", "max-age=600"],
        when=lambda req, _: req.params.keys() <= CACHED_COMMANDS,
    )
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self.api_fragment_info_schema.dump(
            self._dispatch(req.params)(
                req.context.user.get_scopes(prefix="read:", suffix="-fragments")
            )
        )
