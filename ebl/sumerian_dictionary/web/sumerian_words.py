import time
from typing import Generic, Sequence, TypeVar

import attr
import falcon
from falcon import Request, Response
from falcon_caching import Cache

from ebl.cache.application.cache import DAILY_TIMEOUT, DEFAULT_TIMEOUT, cache_control
from ebl.dispatcher import DispatchError
from ebl.sumerian_dictionary.application.sumerian_word_repository import (
    SumerianWordRepository,
)
from ebl.sumerian_dictionary.domain.sumerian_word_summary import Statistics
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordSchema,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_summary_schema import (
    SearchResultSchema,
    StatisticsSchema,
    SumerianWordSummarySchema,
)
from ebl.sumerian_dictionary.web.sumerian_word_query_parameters import (
    parse_search_query,
)
from ebl.users.web.require_scope import require_scope

READ_SCOPE = "read:sumerian-words"
IDS_PARAMETER = "ids"

T = TypeVar("T")


@attr.s(frozen=True, auto_attribs=True)
class Snapshot(Generic[T]):
    computed_at: float
    value: T

    @property
    def age_in_seconds(self) -> int:
        return max(0, int(time.time() - self.computed_at))


def _respond_with_snapshot(resp: Response, snapshot: Snapshot, media: object) -> None:
    resp.set_header("Age", str(snapshot.age_in_seconds))
    resp.media = media


class SumerianWordResource:
    def __init__(self, repository: SumerianWordRepository) -> None:
        self._repository = repository

    @falcon.before(require_scope, READ_SCOPE)
    def on_get(self, _req: Request, resp: Response, word_id: str) -> None:
        resp.media = SumerianWordSchema().dump(self._repository.find(word_id))


class SumerianWordSearchResource:
    def __init__(self, repository: SumerianWordRepository) -> None:
        self._repository = repository

    @falcon.before(require_scope, READ_SCOPE)
    def on_get(self, req: Request, resp: Response) -> None:
        if IDS_PARAMETER in req.params:
            resp.media = SumerianWordSummarySchema(many=True).dump(
                self._repository.find_summaries(self._ids(req))
            )
        else:
            resp.media = SearchResultSchema().dump(
                self._repository.search(parse_search_query(req))
            )

    def _ids(self, req: Request) -> Sequence[str]:
        if set(req.params) != {IDS_PARAMETER}:
            raise DispatchError(f"Invalid parameters {sorted(req.params)}.")
        values = req.get_param_as_list(IDS_PARAMETER) or []
        return [
            identifier
            for value in values
            for identifier in value.split(",")
            if identifier
        ]


class SumerianWordListResource:
    def __init__(self, repository: SumerianWordRepository, cache: Cache) -> None:
        @cache.memoize(DEFAULT_TIMEOUT)
        def list_sumerian_word_ids() -> Snapshot[Sequence[str]]:
            return Snapshot(time.time(), repository.list_ids())

        self._list_ids = list_sumerian_word_ids

    @falcon.before(require_scope, READ_SCOPE)
    @cache_control(["private", f"max-age={DEFAULT_TIMEOUT}"])
    def on_get(self, _req: Request, resp: Response) -> None:
        snapshot = self._list_ids()
        _respond_with_snapshot(resp, snapshot, list(snapshot.value))


class SumerianWordStatisticsResource:
    def __init__(self, repository: SumerianWordRepository, cache: Cache) -> None:
        @cache.memoize(DAILY_TIMEOUT)
        def sumerian_word_statistics() -> Snapshot[Statistics]:
            return Snapshot(time.time(), repository.statistics())

        self._statistics = sumerian_word_statistics

    @falcon.before(require_scope, READ_SCOPE)
    @cache_control(["private", f"max-age={DAILY_TIMEOUT}"])
    def on_get(self, _req: Request, resp: Response) -> None:
        snapshot = self._statistics()
        _respond_with_snapshot(resp, snapshot, StatisticsSchema().dump(snapshot.value))
