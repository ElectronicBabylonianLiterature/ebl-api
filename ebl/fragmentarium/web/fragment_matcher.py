from falcon import Request, Response

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)


class FragmentMatcherResource:
    def __init__(self, fragment_matcher: FragmentMatcher):
        self.fragment_matcher = fragment_matcher

    def on_get(self, req: Request, resp: Response, number) -> None:
        try:
            resp.media = LineToVecRankingSchema().dump(
                self.fragment_matcher.rank_line_to_vec(number)
            )
        except (ValueError, NotFoundError) as error:
            raise DataError(error) from error
