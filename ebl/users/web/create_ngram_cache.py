from ebl.fragmentarium.infrastructure.fragment_ngram_repository import (
    FragmentNGramRepository,
)


NGRAM_LENGHTS = [1, 2, 3]


def create_fragment_ngram_cache(_req, resp, resource):
    museum_number_dto = resp.media["museumNumber"]

    ngram_repository: FragmentNGramRepository = resource.ngram_repository
    ngram_repository.update_ngrams(museum_number_dto, NGRAM_LENGHTS)
