from marshmallow import EXCLUDE
from ebl.common.infrastructure.ngrams import DEFAULT_N
from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.infrastructure.corpus_ngram_repository import ChapterNGramRepository
from ebl.fragmentarium.infrastructure.fragment_ngram_repository import (
    FragmentNGramRepository,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


def create_fragment_ngram_cache(_req, resp, resource):
    if museum_number_dto := resp.media.get("museumNumber"):
        ngram_repository: FragmentNGramRepository = resource.ngram_repository
        ngram_repository.set_ngrams(
            MuseumNumberSchema().load(museum_number_dto), DEFAULT_N
        )


def create_chapter_ngram_cache(_req, resp, resource):
    ngram_repository: ChapterNGramRepository = resource.ngram_repository
    chapter_id = ChapterIdSchema().load(resp.media, unknown=EXCLUDE)
    ngram_repository.set_ngrams(chapter_id, DEFAULT_N)
