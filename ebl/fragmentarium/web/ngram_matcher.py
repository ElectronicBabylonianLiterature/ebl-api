from falcon import Request, Response
from ebl.fragmentarium.infrastructure.fragment_ngram_repository import (
    FragmentNGramRepository,
)

DEFAULT_N = [1, 2, 3]


class NgramAlignResource:
    def __init__(
        self,
        ngram_repository: FragmentNGramRepository,
    ):
        self.ngram_repository = ngram_repository

    def on_get(self, _req: Request, resp: Response, number: str) -> None:
        N = _req.get_param_as_list("n", transform=int, default=DEFAULT_N)
        resp.media = list(self.ngram_repository.get_or_set_ngrams(number, N))
