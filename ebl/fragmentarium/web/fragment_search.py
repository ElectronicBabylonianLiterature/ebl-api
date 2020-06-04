import falcon  # pyre-ignore
import pydash  # pyre-ignore

from ebl.dispatcher import create_dispatcher
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_query_factory import (
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
    ):
        self._dispatch = create_dispatcher(
            {
                "reference": lambda query: finder.search_references(*query.values()),
                "number": finder.search,
                "random": lambda _: finder.find_random(),
                "interesting": lambda _: finder.find_interesting(),
                "latest": lambda _: fragmentarium.find_latest(),
                "needsRevision": lambda _: fragmentarium.find_needs_revision(),
                "transliteration": pydash.flow(
                    transliteration_query_factory.create, finder.search_transliteration,
                ),
            }
        )



    @falcon.before(require_scope, "read:fragments")
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:  # pyre-ignore[11]
        """---
        description: >-
          Finds fragments matching the given query.
          Exactly one query parameter must be given.

        responses:
          200:
            description: Fragments matching the query
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/FragmentInfo'
          422:
            description: Incorrect number of query parameters
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: query
          name: number
          schema:
            type: string
        - in: query
          name: random
          schema:
            type: boolean
        - in: query
          name: interesting
          schema:
            type: boolean
        - in: query
          name: latest
          schema:
            type: boolean
        - in: query
          name: needsRevision
          schema:
            type: boolean
        - in: query
          name: transliteration
          schema:
            type: string
        """
        infos = self._dispatch(req.params)
        resp.media = FragmentInfoSchema(many=True).dump(infos)  # pyre-ignore[16,28]
        if req.params.keys() <= CACHED_COMMANDS:
            resp.cache_control = ["private", "max-age=600"]
