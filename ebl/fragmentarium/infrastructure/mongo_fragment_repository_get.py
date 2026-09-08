from typing import Optional, Sequence, Union, cast

from marshmallow import EXCLUDE
from pymongo.collation import Collation

from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult, AfORegisterToFragmentQueryResult
from ebl.common.query.query_schemas import (
    AfORegisterToFragmentQueryResultSchema,
)
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQueryResult
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get_summary import (
    MongoFragmentRepositoryGetSummary,
    load_museum_number,
    load_query_result,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_pipelines import (
    aggregate_counts,
    chapter_lemma_pipeline,
    filter_fragment_lines,
    fragment_lemma_pipeline,
    omit_text_lines,
)
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_latest,
    join_joins,
    join_findspots,
    aggregate_by_traditional_references,
)
from ebl.fragmentarium.infrastructure.queries import match_user_scopes
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.queries import query_number_is
from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get_extended import (
    MongoFragmentRepositoryGetExtended,
)

RETRIEVE_ALL_LIMIT = 1000


class MongoFragmentRepositoryGetBase(MongoFragmentRepositoryGetSummary):
    def query_by_museum_number(
        self,
        number: Union[MuseumNumber, ExcavationNumber],
        lines: Optional[Sequence[int]] = None,
        exclude_lines: bool = False,
    ) -> Fragment:
        data = self._fragments.aggregate(
            [
                {"$match": query_number_is(number)},
                *(omit_text_lines() if exclude_lines else filter_fragment_lines(lines)),
                *join_findspots(),
                *join_reference_documents(),
                *join_joins(),
            ]
        )
        try:
            fragment_data = next(data)
            return cast(Fragment, self._schema(unknown=EXCLUDE).load(fragment_data))
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def query_museum_numbers(self, prefix: str, number_regex: str) -> Sequence[dict]:
        return list(
            self._fragments.find_many(
                {
                    "museumNumber.prefix": prefix,
                    "museumNumber.number": {"$regex": number_regex},
                },
                projection={"museumNumber": True},
            )
        )

    def query_by_sort_key(self, key: int) -> MuseumNumber:
        if key < 0:
            last_fragment = next(
                self._fragments.find_many(
                    {}, projection={"_sortKey": True, "museumNumber": True}
                )
                .sort("_sortKey", -1)
                .limit(1)
            )
            return load_museum_number(last_fragment)

        if match := next(
            self._fragments.aggregate(
                [
                    {"$match": {"_sortKey": {"$in": [0, key]}}},
                    {"$limit": 2},
                    {"$sort": {"_sortKey": -1}},
                    {"$project": {"museumNumber": True}},
                ]
            ),
            None,
        ):
            return load_museum_number(match)
        else:
            raise NotFoundError(f"Unable to find fragment with _sortKey {key}")

    def query_next_and_previous_fragment(
        self, museum_number: MuseumNumber
    ) -> FragmentPagerInfo:
        current = self._fragments.find_one(
            {
                "museumNumber.prefix": museum_number.prefix,
                "museumNumber.number": museum_number.number,
                "museumNumber.suffix": museum_number.suffix,
            },
            projection={"_sortKey": True},
        ).get("_sortKey")

        if current is None:
            prev = next_ = museum_number
        else:
            prev = self.query_by_sort_key(current - 1)
            next_ = self.query_by_sort_key(current + 1)

        return FragmentPagerInfo(prev, next_)

    def query(
        self, query: dict, user_scopes: Sequence[Scope] = ()
    ) -> Union[QueryResult, FragmentQueryResult]:
        cursor = (
            self._fragments.aggregate(
                PatternMatcher(
                    query, self._provenance_service, user_scopes
                ).build_pipeline(),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
                allowDiskUse=True,
            )
            if set(query) - {"lemmaOperator"}
            else iter([])
        )
        return (
            self._load_fragment_query_result(next(cursor, None))
            if "limit" in query
            else load_query_result(cursor)
        )

    def query_latest(self) -> QueryResult:
        return load_query_result(
            self._fragments.aggregate(
                aggregate_latest(),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
            )
        )

    def query_by_traditional_references(
        self,
        traditional_references: Sequence[str],
        user_scopes: Sequence[Scope] = (),
    ) -> AfORegisterToFragmentQueryResult:
        pipeline = aggregate_by_traditional_references(
            traditional_references, user_scopes
        )
        data = self._fragments.aggregate(pipeline)
        return (
            cast(
                AfORegisterToFragmentQueryResult,
                AfORegisterToFragmentQueryResultSchema().load({"items": data}),
            )
            if data
            else AfORegisterToFragmentQueryResult.create_empty()
        )

    def list_all_fragments(self, user_scopes: Sequence[Scope] = ()) -> Sequence[str]:
        return list(
            self._fragments.get_all_values("_id", match_user_scopes(user_scopes))
        )

    def retrieve_transliterated_fragments(self, skip: int) -> Sequence[dict]:
        fragments = self._fragments.aggregate(
            [
                {
                    "$match": HAS_TRANSLITERATION
                    | {"authorizedScopes": {"$exists": False}}
                },
                {
                    "$project": {
                        "folios": 0,
                        "lineToVec": 0,
                        "authorizedScops": 0,
                        "references": 0,
                        "uncuratedReferences": 0,
                        "genreLegacy": 0,
                        "legacyJoins": 0,
                        "legacyScript": 0,
                        "_sortKey": 0,
                    }
                },
                {"$skip": skip},
                {"$limit": RETRIEVE_ALL_LIMIT},
            ]
        )
        return list(fragments)

    def collect_lemmas(self, number: MuseumNumber):
        fragment = self.query_by_museum_number(number)
        clean_values = list(
            {
                token.clean_value
                for line in fragment.text.text_lines
                for token in line.content
                if token.lemmatizable
            }
        )
        return {
            element["_id"]: max(
                element["lemmatizations"], key=lambda entry: entry["count"]
            )["uniqueLemma"]
            for element in self._fragments.aggregate(
                [
                    *fragment_lemma_pipeline(clean_values),
                    {
                        "$unionWith": {
                            "coll": "chapters",
                            "pipeline": chapter_lemma_pipeline(clean_values),
                        }
                    },
                    *aggregate_counts(),
                ]
            )
        }


class MongoFragmentRepositoryGet(
    MongoFragmentRepositoryGetBase, MongoFragmentRepositoryGetExtended
):
    pass
