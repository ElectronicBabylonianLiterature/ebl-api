from typing import Tuple, Optional

import falcon
from falcon_caching import Cache

from ebl.cache import DEFAULT_TIMEOUT, cache_control
from ebl.dispatcher import create_dispatcher
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_info_schema import ApiFragmentInfoSchema
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
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
        def find_needs_revision(_):
            return fragmentarium.find_needs_revision()

        @cache.memoize(DEFAULT_TIMEOUT)
        def find_latest(_):
            return fragmentarium.find_latest()

        self._transliteration_query_factory = transliteration_query_factory
        self._dispatch = create_dispatcher(
            {
                frozenset(
                    ["number", "transliteration", "id", "pages"]
                ): lambda value: finder.search_fragmentarium(
                    *self._parse_fragmentarium_search(**value)
                ),
                frozenset(["random"]): lambda _: finder.find_random(),
                frozenset(["interesting"]): lambda _: finder.find_interesting(),
                frozenset(["latest"]): find_latest,
                frozenset(["needsRevision"]): find_needs_revision,
            }
        )

    def _parse_fragmentarium_search(
        self, number: str, transliteration: str, id: str, pages: str
    ) -> Tuple[str, Optional[TransliterationQuery], str, str]:
        parsed_transliteration = (
            self._transliteration_query_factory.create(transliteration)
            if transliteration
            else None
        )
        validated_id, validated_pages = self._validate_pages(id, pages)

        return number, parsed_transliteration, validated_id, validated_pages

    @staticmethod
    def _validate_pages(id: str, pages: str) -> Tuple[str, str]:
        if pages and not id:
            raise DataError("Name, Year or Title required")
        if pages and id:
            try:
                int(pages)
            except ValueError as error:
                raise DataError(f'Pages "{pages}" not numeric.') from error
        return id, pages

    @falcon.before(require_scope, "read:fragments")
    @cache_control(  # pyre-ignore[56]
        ["private", "max-age=600"],
        when=lambda req, _: req.params.keys() <= CACHED_COMMANDS,
    )
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        print(req.params)
        infos = self._dispatch(req.params)
        resp.media = ApiFragmentInfoSchema(many=True).dump(infos)
