from falcon import Request, Response, falcon  # pyre-ignore[21]

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.users.web.require_scope import require_scope


class FragmentMatcherResource:
    def __init__(self, fragment_matcher: FragmentMatcher):
        self.fragment_matcher = fragment_matcher

    @falcon.before(require_scope, "transliterate:fragments")  # pyre-ignore[56]
    # pyre-ignore[11]
    def on_get(self, req: Request, resp: Response, number) -> None:
        try:
            if number.startswith("[") and number.endswith("]"):
                number = number.replace("[", "").replace("]", "").split(",")
                number = tuple([int(x.strip()) for x in number])

            resp.media = LineToVecRankingSchema().dump(  # pyre-ignore[16]
                self.fragment_matcher.rank_line_to_vec(number)
            )
        except (ValueError, NotFoundError) as error:
            raise DataError(error)
