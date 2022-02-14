from typing import Tuple, Union

import falcon
from falcon_caching import Cache

from ebl.cache import DEFAULT_TIMEOUT
from ebl.dispatcher import create_dispatcher
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_info_schema import ApiFragmentInfoSchema
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.users.web.require_scope import require_scope

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
        def find_interesting(_):
            return finder.find_interesting()

        @cache.memoize(DEFAULT_TIMEOUT)
        def find_latest(_):
            return fragmentarium.find_latest()

        self._dispatch = create_dispatcher(
            {
                frozenset(
                    ["id", "pages"]
                ): lambda value: finder.search_references_in_fragment_infos(
                    *self._validate_pages(**value)
                ),
                frozenset(["number"]): lambda value: finder.search(**value),
                frozenset(["random"]): lambda _: finder.find_random(),
                frozenset(["interesting"]): find_interesting,
                frozenset(["latest"]): find_latest,
                frozenset(
                    ["needsRevision"]
                ): lambda _: fragmentarium.find_needs_revision(),
                frozenset(
                    ["transliteration"]
                ): lambda value: finder.search_transliteration(
                    transliteration_query_factory.create(**value)
                ),
            }
        )

    @staticmethod
    def _validate_pages(id: str, pages: Union[str, None]) -> Tuple[str, str]:
        if pages:
            try:
                int(pages)
                return id, pages
            except ValueError as error:
                raise DataError(f'Pages "{pages}" not numeric.') from error
        else:
            return id, ""

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        infos = self._dispatch(req.params)
        resp.media = ApiFragmentInfoSchema(many=True).dump(infos)
        if req.params.keys() <= CACHED_COMMANDS:
            resp.cache_control = ["private", "max-age=600"]
