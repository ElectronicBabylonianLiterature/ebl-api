from falcon import Request, Response
from ebl.common.infrastructure.ngrams import DEFAULT_N
from ebl.corpus.infrastructure.corpus_ngram_repository import ChapterNGramRepository
from ebl.fragmentarium.infrastructure.fragment_ngram_repository import (
    FragmentNGramRepository,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


class NgramAlignResource:
    def __init__(
        self,
        ngram_repository: FragmentNGramRepository,
        chapter_ngram_repository: ChapterNGramRepository,
    ):
        self.ngram_repository = ngram_repository
        self.chapter_ngram_repository = chapter_ngram_repository

    def on_get(self, _req: Request, resp: Response, number: str) -> None:
        N = _req.get_param_as_list("n", transform=int, default=DEFAULT_N)
        ngrams = self.ngram_repository.get_or_set_ngrams(MuseumNumber.of(number), N)
        resp.media = self.chapter_ngram_repository.compute_overlaps(ngrams)
