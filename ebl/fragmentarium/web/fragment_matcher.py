from falcon import Request, Response, falcon  # pyre-ignore[21]

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.users.web.require_scope import require_scope


class FragmentMatcherResource:
    def __init__(self, fragment_matcher: FragmentMatcher):
        self.fragment_matcher = fragment_matcher

    @falcon.before(require_scope, "transliterate:fragments")  # pyre-ignore[56]
    # pyre-ignore[11]
    def on_get(self, req: Request, resp: Response, number) -> None:
        if number.startswith("[") and number.endswith("]"):
            number = number.replace("[", "").replace("]", "").split(",")
            try:
                number = tuple([int(x.strip()) for x in number])
            except ValueError as error:
                DataError(error)
        result = self.fragment_matcher.line_to_vec(number)
        resp.media = {
            "score": result["score"],
            "scoreWeighted": result["score_weighted"],
        }
