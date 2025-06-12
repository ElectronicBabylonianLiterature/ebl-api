from typing import List, Optional, Tuple, Sequence, Dict, TypedDict, cast
from pymongo.collation import Collation

from ebl.common.query.query_result import CorpusQueryResult
from ebl.common.query.query_schemas import CorpusQueryResultSchema
from ebl.corpus.application.schemas import (
    ChapterSchema,
    DictionaryLineSchema,
    ManuscriptSchema,
    ManuscriptAttestationSchema,
    UncertainFragmentAttestationSchema,
)
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)
from ebl.corpus.infrastructure.chapter_query_filters import (
    filter_query_by_transliteration,
)
from ebl.corpus.infrastructure.corpus_search_aggregations import CorpusPatternMatcher
from ebl.corpus.infrastructure.manuscript_lemma_filter import (
    filter_manuscripts_by_lemma,
)
from ebl.corpus.infrastructure.queries import (
    chapter_id_query,
    join_text,
    join_text_title,
)
from ebl.errors import NotFoundError
from ebl.fragmentarium.infrastructure.queries import is_in_fragmentarium, join_joins
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    MongoTextRepositoryBase,
    chapter_not_found,
)
from ebl.corpus.application.text_repository import CorpusFragmentsMapping

class MuseumNumberMapping(TypedDict):
    prefix: str
    number: str
    suffix: str


def get_museum_number_mappings(
    museum_numbers: Sequence[MuseumNumber],
) -> List[MuseumNumberMapping]:
    return [
        cast(
            MuseumNumberMapping,
            {
                "prefix": museum_number["prefix"],
                "number": museum_number["number"],
                "suffix": museum_number["suffix"],
            },
        )
        for museum_number in MuseumNumberSchema().dump(museum_numbers, many=True)
    ]


class MongoTextRepositoryQuery(MongoTextRepositoryBase):
    def query_by_transliteration(
        self, query: TransliterationQuery, pagination_index: int
    ) -> Tuple[Sequence[Chapter], int]:
        LIMIT = 30
        mongo_query = {"signs": {"$regex": query.regexp}}
        cursor = self._chapters.aggregate(
            [
                {"$match": mongo_query},
                {
                    "$lookup": {
                        "from": "texts",
                        "let": {
                            "chapterGenre": "$textId.genre",
                            "chapterCategory": "$textId.category",
                            "chapterIndex": "$textId.index",
                        },
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$genre", "$$chapterGenre"]},
                                            {"$eq": ["$category", "$$chapterCategory"]},
                                            {"$eq": ["$index", "$$chapterIndex"]},
                                        ]
                                    }
                                }
                            },
                            {"$project": {"name": 1, "_id": 0}},
                        ],
                        "as": "textNames",
                    }
                },
                {"$project": {"_id": False}},
                {"$addFields": {"textName": {"$first": "$textNames"}}},
                {"$addFields": {"textName": "$textName.name"}},
                {"$project": {"textNames": False}},
                {"$skip": LIMIT * pagination_index},
                {"$limit": LIMIT},
            ],
            allowDiskUse=True,
        )
        return ChapterSchema().load(
            filter_query_by_transliteration(query, cursor), many=True
        ), self._chapters.count_documents(mongo_query)

    def _limit_by_genre(self, cursor: Sequence[Dict]) -> List[Dict]:
        LIMIT = 10
        limited_lines = []
        genre_counts = {genre.value: 0 for genre in Genre}

        for line_dto in cursor:
            genre = line_dto["textId"]["genre"]
            if genre_counts[genre] < LIMIT:
                limited_lines.append(line_dto)
                genre_counts[genre] += 1
            if sum(genre_counts.values()) >= 40:
                break

        return limited_lines

    def query_by_lemma(
        self, lemma: str, genre: Optional[Genre] = None
    ) -> Sequence[DictionaryLine]:
        lemma_query = {
            "$or": [
                {"lines.variants.reconstruction.uniqueLemma": lemma},
                {"lines.variants.manuscripts.line.content.uniqueLemma": lemma},
            ],
        }

        if genre is not None:
            lemma_query["textId.genre"] = genre.value

        lemma_lines = self._chapters.aggregate(
            [
                {"$match": lemma_query},
                {
                    "$project": {
                        "_id": False,
                        "lines": True,
                        "name": True,
                        "stage": True,
                        "textId": True,
                        "manuscripts": True,
                    }
                },
                {"$unwind": "$lines"},
                {"$match": lemma_query},
                join_text_title(),
                filter_manuscripts_by_lemma(lemma),
                {
                    "$project": {
                        "textId": True,
                        "textName": {"$first": "$textName.name"},
                        "chapterName": "$name",
                        "stage": True,
                        "line": "$lines",
                        "manuscripts": True,
                    }
                },
            ]
        )

        return DictionaryLineSchema().load(
            self._limit_by_genre(lemma_lines),
            many=True,
        )

    def query(self, query: dict) -> CorpusQueryResult:
        if set(query) - {"lemmaOperator"}:
            matcher = CorpusPatternMatcher(query)
            data = next(
                self._chapters.aggregate(
                    matcher.build_pipeline(),
                    collation=Collation(
                        locale="en", numericOrdering=True, alternate="shifted"
                    ),
                    allowDiskUse=True,
                ),
                None,
            )
        else:
            data = None

        return (
            CorpusQueryResultSchema().load(data)
            if data
            else CorpusQueryResult.create_empty()
        )

    def query_manuscripts_by_chapter(self, id_: ChapterId) -> List[Manuscript]:
        try:
            return ManuscriptSchema().load(
                self._chapters.find_one(
                    chapter_id_query(id_), projection={"manuscripts": True}
                )["manuscripts"],
                many=True,
            )
        except NotFoundError as error:
            raise chapter_not_found(id_) from error

    def query_manuscripts_with_joins_by_chapter(
        self, id_: ChapterId
    ) -> List[Manuscript]:
        try:
            return ManuscriptSchema().load(
                self._chapters.aggregate(
                    [
                        {"$match": chapter_id_query(id_)},
                        {"$project": {"manuscripts": True}},
                        {"$unwind": "$manuscripts"},
                        {"$replaceRoot": {"newRoot": "$manuscripts"}},
                        *join_joins(),
                        *is_in_fragmentarium("museumNumber", "isInFragmentarium"),
                    ]
                ),
                many=True,
            )
        except NotFoundError as error:
            raise chapter_not_found(id_) from error

    def query_corpus_by_manuscripts(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[ManuscriptAttestation]:
        cursor = self._chapters.aggregate(
            [
                {"$unwind": "$manuscripts"},
                {
                    "$set": {
                        "museumNumbers": {
                            "prefix": "$manuscripts.museumNumber.prefix",
                            "number": "$manuscripts.museumNumber.number",
                            "suffix": "$manuscripts.museumNumber.suffix",
                        }
                    }
                },
                {
                    "$match": {
                        "museumNumbers": {
                            "$in": get_museum_number_mappings(museum_numbers)
                        }
                    },
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "chapterId": {
                                "textId": "$textId",
                                "stage": "$stage",
                                "name": "$name",
                            },
                            "manuscript": "$manuscripts",
                        }
                    }
                },
                *join_text(),
                {"$unwind": "$text"},
            ]
        )
        return ManuscriptAttestationSchema().load(cursor, many=True)

    def query_corpus_by_uncertain_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[UncertainFragmentAttestation]:
        cursor = self._chapters.aggregate(
            [
                {"$unwind": "$uncertainFragments"},
                {
                    "$set": {
                        "museumNumbers": {
                            "prefix": "$uncertainFragments.prefix",
                            "number": "$uncertainFragments.number",
                            "suffix": "$uncertainFragments.suffix",
                        }
                    }
                },
                {
                    "$match": {
                        "museumNumbers": {
                            "$in": get_museum_number_mappings(museum_numbers)
                        }
                    },
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "chapterId": {
                                "textId": "$textId",
                                "stage": "$stage",
                                "name": "$name",
                            },
                            "museumNumber": "$uncertainFragments",
                        }
                    }
                },
                *join_text(),
                {"$unwind": "$text"},
            ]
        )
        cursor = list(cursor)
        # ToDo: Fix issue here and clean up
        print(cursor)
        input()
        return UncertainFragmentAttestationSchema().load(cursor, many=True)

    def query_corpus_by_related_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> CorpusFragmentsMapping:
        return {
            "manuscripts": self.query_corpus_by_manuscripts(museum_numbers),
            "uncertain_fragments": self.query_corpus_by_uncertain_fragments(
                museum_numbers
            ),
        }
