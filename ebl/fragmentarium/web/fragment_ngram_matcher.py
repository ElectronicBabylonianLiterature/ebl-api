from ebl.corpus.application.text_repository import TextRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from falcon import Request, Response

from ebl.transliteration.domain.museum_number import MuseumNumber


class NgramMatcherResource:
    def __init__(
        self,
        fragment_repository: FragmentRepository,
        text_repository: TextRepository,
    ):
        self._fragment_repository = fragment_repository
        self._text_repository = text_repository

    def on_get(self, _req: Request, resp: Response, number: str) -> None:
        ngrams = self._fragment_repository.get_ngrams(MuseumNumber.of(number))
        resp.media = self._text_repository.aggregate_ngram_overlaps(ngrams)
