from typing import List, Mapping, Sequence, Tuple, cast

from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.sumerian_dictionary.application.sumerian_word_repository import (
    SumerianWordRepository,
)
from ebl.sumerian_dictionary.domain.search_query import SumerianWordQuery
from ebl.sumerian_dictionary.domain.sumerian_word import SumerianWord
from ebl.sumerian_dictionary.domain.sumerian_word_summary import (
    SearchResult,
    Statistics,
    SumerianWordSummary,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_pipeline import (
    MANAGED_DOCUMENT,
    search_match,
    search_projection,
    statistics_counts,
    statistics_pipeline,
    summary_projection,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_search_ranking import (
    MatchRank,
    SumerianRelevanceRanker,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_links import (
    fetch_link_targets,
    linked_ids,
    resolve_links,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordDocumentSchema,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_summary_schema import (
    StatisticsSchema,
    SumerianWordSummarySchema,
)

COLLECTION = "words-sumerian"
INDEXED_FIELDS: Sequence[str] = (
    "citationForm",
    "lemma",
    "aliases.form",
    "guideWord",
    "pos",
    "sources.attinger.entryId",
    "sources.epsd2.oid",
)

RankedDocument = Tuple[MatchRank, Mapping[str, object]]


class MongoSumerianWordRepository(SumerianWordRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        for field in INDEXED_FIELDS:
            self._collection.create_index(field)

    def find(self, id_: str) -> SumerianWord:
        try:
            document = self._collection.find_one({"_id": id_, **MANAGED_DOCUMENT})
        except NotFoundError:
            raise NotFoundError(f"Sumerian word '{id_}' not found.")
        word = cast(SumerianWord, SumerianWordDocumentSchema().load(document))
        targets = fetch_link_targets(self._collection, linked_ids(word))
        return resolve_links(word, targets)

    def search(self, query: SumerianWordQuery) -> SearchResult:
        ranker = SumerianRelevanceRanker(query.query)
        if not ranker.folded_query:
            return SearchResult(0, ())
        ranked = self._rank(ranker, self._candidates(query, ranker.folded_query))
        start = query.offset
        end = start + query.limit
        page = ranked[start:end]
        return SearchResult(
            len(ranked),
            tuple(self._summary(ranker, document) for _, document in page),
        )

    def find_summaries(self, ids: Sequence[str]) -> Sequence[SumerianWordSummary]:
        documents = self._collection.aggregate(
            [
                {"$match": {"$and": [MANAGED_DOCUMENT, {"_id": {"$in": list(ids)}}]}},
                {"$project": summary_projection()},
            ]
        )
        summaries = {
            summary.id: summary
            for summary in cast(
                List[SumerianWordSummary],
                SumerianWordSummarySchema(many=True).load(documents),
            )
        }
        return tuple(summaries[id_] for id_ in ids if id_ in summaries)

    def list_ids(self) -> Sequence[str]:
        return self._collection.get_all_values("_id", MANAGED_DOCUMENT)

    def statistics(self) -> Statistics:
        facets = next(self._collection.aggregate(statistics_pipeline()))
        return cast(Statistics, StatisticsSchema().load(statistics_counts(facets)))

    def _candidates(
        self, query: SumerianWordQuery, folded_query: str
    ) -> List[Mapping[str, object]]:
        return list(
            self._collection.aggregate(
                [
                    {"$match": search_match(query, folded_query)},
                    {"$project": search_projection()},
                ]
            )
        )

    def _rank(
        self,
        ranker: SumerianRelevanceRanker,
        documents: Sequence[Mapping[str, object]],
    ) -> List[RankedDocument]:
        ranked = [
            (rank, document)
            for document in documents
            for rank in [ranker.rank(document)]
            if rank is not None
        ]
        return sorted(ranked, key=lambda pair: ranker.key(*pair))

    def _summary(
        self, ranker: SumerianRelevanceRanker, document: Mapping[str, object]
    ) -> SumerianWordSummary:
        return cast(
            SumerianWordSummary,
            SumerianWordSummarySchema().load(
                {**document, "matchedAlias": ranker.alias_hit(document)}
            ),
        )
