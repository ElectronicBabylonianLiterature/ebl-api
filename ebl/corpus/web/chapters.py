from collections import defaultdict
from typing import Sequence, Optional
import falcon
from pydash.arrays import flatten_deep
from pydash import flow

from ebl.cache.application.custom_cache import ChapterCache
from ebl.common.query.parameter_parser import (
    parse_lemmas,
    parse_transliteration,
    parse_lines,
)
from ebl.common.query.query_schemas import CorpusQueryResultSchema
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.application.schemas import (
    ManuscriptAttestationSchema,
)
from ebl.corpus.domain.dictionary_display import DictionaryLineDisplay
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.display_schemas import DictionaryLineDisplaySchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.domain.stage import Stage


class ChaptersResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

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
    def __init__(self, corpus: Corpus, cache: ChapterCache):
        self._corpus = corpus
        self._cache = cache

    def _create_line_variant_map(
        self, lines: Sequence[int], variants: Sequence[int]
    ) -> dict:
        line_variants = defaultdict(set)

        for line, variant in zip(lines, variants):
            line_variants[line].add(variant)

        return line_variants

    def _select_lines_and_variants(
        self,
        chapter: dict,
        lines: Optional[Sequence[int]],
        variants: Optional[Sequence[int]],
    ):
        if lines and variants:
            line_variants_map = self._create_line_variant_map(lines, variants)

            def get_matching_variants(variants: Sequence, line_index) -> Sequence:
                return [variants[i] for i in line_variants_map[line_index]]

            chapter["lines"] = [
                {
                    **line,
                    "variants": get_matching_variants(line["variants"], line_index),
                }
                for line_index, line in enumerate(chapter["lines"])
                if line_index in lines
            ]

        return chapter

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        chapter_id_str = str(chapter_id)
        lines = parse_lines(req.get_param_as_list("lines", default=[]))
        variants = parse_lines(req.get_param_as_list("variants", default=[]))

        if self._cache.has(chapter_id_str):
            cached_chapter = self._cache.get(chapter_id_str)
            resp.media = self._select_lines_and_variants(
                cached_chapter, lines, variants
            )
        else:
            chapter = self._corpus.find_chapter_for_display(chapter_id)
            dump = ChapterDisplaySchema().dump(chapter)
            self._cache.set(chapter_id_str, dump)

            resp.media = self._select_lines_and_variants(dump, lines, variants)


class ChaptersByManuscriptResource:
    def __init__(self, corpus: Corpus, fragment_finder: FragmentFinder):
        self._corpus = corpus
        self._fragment_finder = fragment_finder

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

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        genre = req.params.get("genre")
        dictionary_lines = self._corpus.search_lemma(
            req.params["lemma"], Genre(genre) if genre else None
        )

        resp.media = DictionaryLineDisplaySchema().dump(
            [
                DictionaryLineDisplay.from_dictionary_line(line)
                for line in dictionary_lines
            ],
            many=True,
        )


class CorpusQueryResource:
    def __init__(
        self,
        corpus: Corpus,
        transliteration_query_factory: TransliterationQueryFactory,
    ):
        self._corpus = corpus
        self._transliteration_query_factory = transliteration_query_factory

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        parse = flow(
            parse_lemmas, parse_transliteration(self._transliteration_query_factory)
        )

        resp.media = CorpusQueryResultSchema().dump(
            self._corpus.query(parse(req.params))
        )


class ChaptersAllResource:
    def __init__(
        self,
        corpus: Corpus,
    ):
        self._corpus = corpus

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        result = self._corpus.list_all_chapters()
        resp.media = [
            {**chapter, **{"stage": Stage.from_name(chapter["stage"]).abbreviation}}
            for chapter in result
        ]


class ChapterSignsResource:
    def __init__(
        self,
        corpus: Corpus,
    ):
        self._corpus = corpus

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        resp.media = self._corpus.get_sign_data(chapter_id)
