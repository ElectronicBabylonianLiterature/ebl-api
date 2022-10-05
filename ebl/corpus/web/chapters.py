import falcon
from pydash.arrays import flatten_deep
from ebl.corpus.application.corpus import Corpus
from ebl.transliteration.domain.genre import Genre
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.application.schemas import (
    DictionaryLinePaginationSchema,
    ManuscriptAttestationSchema,
)
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.users.web.require_scope import require_scope
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.errors import DataError


class ChaptersResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "read:texts")
    def on_get(
        self,
        _,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(chapter)


class ChaptersDisplayResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "read:texts")
    def on_get(
        self,
        _,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        chapter = self._corpus.find_chapter_for_display(chapter_id)
        resp.media = ChapterDisplaySchema().dump(chapter)


class ChaptersByManuscriptResource:
    def __init__(self, corpus: Corpus, fragment_finder: FragmentFinder):
        self._corpus = corpus
        self._fragment_finder = fragment_finder

    @falcon.before(require_scope, "read:texts")
    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        number: str,
    ) -> None:
        try:
            museum_number = MuseumNumber.of(number)
        except ValueError as error:
            raise DataError(f"Invalid museum number {number}.") from error
        fragment = self._fragment_finder.find(museum_number)[0]
        museum_numbers = [
            join.museum_number for join in flatten_deep(fragment.joins.fragments)
        ] or [museum_number]
        manuscript_attestations = self._corpus.search_corpus_by_manuscript(
            museum_numbers
        )
        resp.media = ManuscriptAttestationSchema().dump(
            manuscript_attestations, many=True
        )


class ChaptersByLemmaResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "read:texts")
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            pagination_index = int(req.params["paginationIndex"])
        except ValueError as error:
            raise DataError("Pagination Index has to be a number") from error

        genre_key = req.params.get("genre")
        resp.media = DictionaryLinePaginationSchema().dump(
            self._corpus.search_lemma(
                req.params["lemma"],
                pagination_index,
                genre_key if genre_key is None else Genre(genre_key),
            ),
            many=True,
        )
