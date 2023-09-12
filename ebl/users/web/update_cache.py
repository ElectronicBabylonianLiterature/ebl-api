from marshmallow import EXCLUDE
from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.infrastructure.corpus_ngram_repository import ChapterNGramRepository
from ebl.fragmentarium.infrastructure.fragment_ngram_repository import (
    FragmentNGramRepository,
)


NGRAM_LENGHTS = [1, 2, 3]


def create_fragment_ngram_cache(_req, resp, resource):
    if museum_number_dto := resp.media.get("museumNumber"):
        ngram_repository: FragmentNGramRepository = resource.ngram_repository
        ngram_repository.update_ngrams(museum_number_dto, NGRAM_LENGHTS)


def create_chapter_ngram_cache(_req, resp, resource):
    ngram_repository: ChapterNGramRepository = resource.ngram_repository
    chapter_id = ChapterIdSchema().load(resp.media, unknown=EXCLUDE)
    ngram_repository.update_ngrams(chapter_id, NGRAM_LENGHTS)
