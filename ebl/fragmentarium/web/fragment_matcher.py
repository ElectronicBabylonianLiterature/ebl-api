from falcon import Request, Response, before

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.users.web.require_scope import require_fragment_scope


class FragmentMatcherResource:
    def __init__(
        self, fragment_matcher: FragmentMatcher, fragment_finder: FragmentFinder
    ):
        self.fragment_matcher = fragment_matcher
        self._finder = fragment_finder

    @before(require_fragment_scope)
    def on_get(self, req: Request, resp: Response, number) -> None:
        try:
            resp.media = LineToVecRankingSchema().dump(
                self.fragment_matcher.rank_line_to_vec(number)
            )
        except (ValueError, NotFoundError) as error:
            raise DataError(error) from error
