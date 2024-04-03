from typing import List, Optional, Sequence, Iterator

from marshmallow import EXCLUDE
from pymongo.collation import Collation

from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult, AfORegisterToFragmentQueryResult
from ebl.common.query.query_schemas import (
    QueryResultSchema,
    AfORegisterToFragmentQueryResultSchema,
)
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
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


def load_museum_number(data: dict) -> MuseumNumber:
    return MuseumNumberSchema().load(data.get("museumNumber", data))


def load_query_result(cursor: Iterator) -> QueryResult:
    data = next(cursor, None)
    return QueryResultSchema().load(data) if data else QueryResult.create_empty()


class MongoFragmentRepositoryGetBase(FragmentRepository):
    def _omit_text_lines(self) -> List:
        return [{"$addFields": {"text.lines": []}}]

    def _filter_fragment_lines(self, lines: Optional[Sequence[int]]) -> List:
        return (
            [
                {
                    "$addFields": {
                        "text.lines": (
                            {
                                "$map": {
                                    "input": lines,
                                    "as": "i",
                                    "in": {"$arrayElemAt": ["$text.lines", "$$i"]},
                                }
                            }
                        )
                    }
                }
            ]
            if lines
            else []
        )

    def query_by_museum_number(
        self,
        number: MuseumNumber,
        lines: Optional[Sequence[int]] = None,
        exclude_lines=False,
    ):
        data = self._fragments.aggregate(
            [
                {"$match": query_number_is(number)},
                *(
                    self._omit_text_lines()
                    if exclude_lines
                    else self._filter_fragment_lines(lines)
                ),
                *join_findspots(),
                *join_reference_documents(),
                *join_joins(),
            ]
        )
        try:
            fragment_data = next(data)
            return FragmentSchema(unknown=EXCLUDE).load(fragment_data)
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def query_museum_numbers(self, prefix: str, number_regex: str) -> Sequence[dict]:
        return self._fragments.find_many(
            {
                "museumNumber.prefix": prefix,
                "museumNumber.number": {"$regex": number_regex},
            },
            projection={"museumNumber": True},
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

    def query(self, query: dict, user_scopes: Sequence[Scope] = tuple()) -> QueryResult:
        cursor = (
            self._fragments.aggregate(
                PatternMatcher(query, user_scopes).build_pipeline(),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
            )
            if set(query) - {"lemmaOperator"}
            else iter([])
        )
        return load_query_result(cursor)

    def query_latest(self, user_scopes: Sequence[Scope] = tuple()) -> QueryResult:
        return load_query_result(
            self._fragments.aggregate(
                aggregate_latest(user_scopes),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
            )
        )

    def query_by_traditional_references(
        self,
        traditional_references: Sequence[str],
        user_scopes: Sequence[Scope] = tuple(),
    ) -> AfORegisterToFragmentQueryResult:
        pipeline = aggregate_by_traditional_references(
            traditional_references, user_scopes
        )
        data = self._fragments.aggregate(pipeline)
        return (
            AfORegisterToFragmentQueryResultSchema().load({"items": data})
            if data
            else AfORegisterToFragmentQueryResult.create_empty()
        )

    def list_all_fragments(
        self, user_scopes: Sequence[Scope] = tuple()
    ) -> Sequence[str]:
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


class MongoFragmentRepositoryGet(
    MongoFragmentRepositoryGetBase, MongoFragmentRepositoryGetExtended
):
    pass
