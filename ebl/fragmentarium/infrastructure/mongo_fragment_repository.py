import operator
from typing import Callable, List, Optional, Sequence, Tuple, cast

import pymongo
from marshmallow import EXCLUDE
from pymongo.collation import Collation

from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema, ScriptSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.fragmentarium.infrastructure.collections import JOINS_COLLECTION
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import (
    PatternMatcher,
)

from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_latest,
    aggregate_needs_revision,
    aggregate_path_of_the_pioneers,
    aggregate_random,
    fragment_is,
    join_joins,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.transliteration.infrastructure.queries import museum_number_is


def has_none_values(dictionary: dict) -> bool:
    return not all(dictionary.values())


def _select_museum_between_two_values(
    museum_number: MuseumNumber,
    current_museum_number: MuseumNumber,
    current_prev_or_next: Optional[MuseumNumber],
    comparator: Callable[[MuseumNumber, MuseumNumber], bool],
) -> Optional[MuseumNumber]:
    if comparator(current_museum_number, museum_number) and (
        not current_prev_or_next
        or comparator(current_prev_or_next, current_museum_number)
    ):
        return current_museum_number
    else:
        return current_prev_or_next


def _min_max_museum_numbers(
    museum_numbers: Sequence[Optional[MuseumNumber]],
) -> Tuple[MuseumNumber, MuseumNumber]:
    filtered_museum_numbers = list(
        cast(Sequence[MuseumNumber], filter(lambda x: x is not None, museum_numbers))
    )
    return min(filtered_museum_numbers), max(filtered_museum_numbers)


def _find_adjacent_museum_number_from_sequence(
    museum_number: MuseumNumber, cursor: Sequence[dict], is_endpoint=False
) -> Tuple[Optional[MuseumNumber], Optional[MuseumNumber]]:
    first = None
    last = None
    current_prev = None
    current_next = None
    for current_cursor in cursor:
        museum_number_dict = current_cursor["museumNumber"]
        # Not use MuseumNumber().load(current_current["museumNumber"]) because of
        # performance reasons
        current_museum_number = MuseumNumber(
            prefix=museum_number_dict["prefix"],
            number=museum_number_dict["number"],
            suffix=museum_number_dict["suffix"],
        )

        current_prev = _select_museum_between_two_values(
            museum_number, current_museum_number, current_prev, operator.lt
        )
        current_next = _select_museum_between_two_values(
            museum_number, current_museum_number, current_next, operator.gt
        )

        if is_endpoint:
            first, last = _min_max_museum_numbers([first, last, current_museum_number])
    if is_endpoint:
        current_prev = current_prev or last
        current_next = current_next or first
    return current_prev, current_next


class MongoFragmentRepository(FragmentRepository):
    def __init__(self, database):
        self._fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._joins = MongoCollection(database, JOINS_COLLECTION)

    def create_indexes(self) -> None:
        self._fragments.create_index(
            [
                ("museumNumber.prefix", pymongo.ASCENDING),
                ("museumNumber.number", pymongo.ASCENDING),
                ("museumNumber.suffix", pymongo.ASCENDING),
            ],
            unique=True,
        )
        self._fragments.create_index([("accession", pymongo.ASCENDING)])
        self._fragments.create_index([("cdliNumber", pymongo.ASCENDING)])
        self._fragments.create_index([("folios.name", pymongo.ASCENDING)])
        self._fragments.create_index(
            [
                ("text.lines.content.value", pymongo.ASCENDING),
                ("text.lines.content.uniqueLemma.0", pymongo.ASCENDING),
            ]
        )
        self._fragments.create_index([("text.lines.type", pymongo.ASCENDING)])
        self._fragments.create_index([("record.type", pymongo.ASCENDING)])
        self._fragments.create_index(
            [
                ("publication", pymongo.ASCENDING),
                ("joins", pymongo.ASCENDING),
                ("collection", pymongo.ASCENDING),
            ]
        )
        self._joins.create_index(
            [
                ("fragments.museumNumber.prefix", pymongo.ASCENDING),
                ("fragments.museumNumber.number", pymongo.ASCENDING),
                ("fragments.museumNumber.suffix", pymongo.ASCENDING),
            ]
        )

    def count_transliterated_fragments(self):
        return self._fragments.count_documents(HAS_TRANSLITERATION)

    def count_lines(self):
        result = self._fragments.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$text.numberOfLines"}}}]
        )
        try:
            return next(result)["total"]
        except StopIteration:
            return 0

    def create(self, fragment):
        return self._fragments.insert_one(
            {
                "_id": str(fragment.number),
                **FragmentSchema(exclude=["joins"]).dump(fragment),
            }
        )

    def create_many(self, fragments: Sequence[Fragment]) -> Sequence[str]:
        schema = FragmentSchema(exclude=["joins"])
        return self._fragments.insert_many(
            [
                {"_id": str(fragment.number), **schema.dump(fragment)}
                for fragment in fragments
            ]
        )

    def create_join(self, joins: Sequence[Sequence[Join]]) -> None:
        self._joins.insert_one(
            {
                "fragments": [
                    {
                        **JoinSchema(exclude=["is_in_fragmentarium"]).dump(join),
                        "group": index,
                    }
                    for index, group in enumerate(joins)
                    for join in group
                ]
            }
        )

    def _filter_fragment_lines(self, lines: Optional[Sequence[int]]) -> List:
        return (
            [
                {
                    "$addFields": {
                        "text.lines": {
                            "$map": {
                                "input": lines,
                                "as": "i",
                                "in": {"$arrayElemAt": ["$text.lines", "$$i"]},
                            }
                        }
                    }
                }
            ]
            if lines
            else []
        )

    def query_by_museum_number(
        self, number: MuseumNumber, lines: Optional[Sequence[int]] = None
    ):
        data = self._fragments.aggregate(
            [
                {"$match": museum_number_is(number)},
                *self._filter_fragment_lines(lines),
                *join_reference_documents(),
                *join_joins(),
            ]
        )
        try:
            fragment_data = next(data)
            return FragmentSchema(unknown=EXCLUDE).load(fragment_data)
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def fetch_scopes(self, number: MuseumNumber) -> List[Scope]:
        fragment = next(
            self._fragments.find_many(
                museum_number_is(number), projection={"authorizedScopes": True}
            ),
            {},
        )
        return [
            Scope.from_string(scope) for scope in fragment.get("authorizedScopes", [])
        ]

    def query_random_by_transliterated(self, user_scopes: Sequence[Scope] = tuple()):
        cursor = self._fragments.aggregate(
            [*aggregate_random(user_scopes), {"$project": {"joins": False}}]
        )

        return self._map_fragments(cursor)

    def query_path_of_the_pioneers(self, user_scopes: Sequence[Scope] = tuple()):
        cursor = self._fragments.aggregate(
            [
                *aggregate_path_of_the_pioneers(user_scopes),
                {"$project": {"joins": False}},
            ]
        )

        return self._map_fragments(cursor)

    def query_transliterated_numbers(self):
        cursor = self._fragments.find_many(
            HAS_TRANSLITERATION, projection=["museumNumber"]
        ).sort("_id", pymongo.ASCENDING)

        return MuseumNumberSchema(many=True).load(
            fragment["museumNumber"] for fragment in cursor
        )

    def query_transliterated_line_to_vec(self) -> List[LineToVecEntry]:
        cursor = self._fragments.find_many(HAS_TRANSLITERATION, {"text": False})
        return [
            LineToVecEntry(
                MuseumNumberSchema().load(fragment["museumNumber"]),
                ScriptSchema().load(fragment["script"]),
                tuple(
                    LineToVecEncoding.from_list(line_to_vec)
                    for line_to_vec in fragment["lineToVec"]
                ),
            )
            for fragment in cursor
        ]

    def query_by_transliterated_sorted_by_date(
        self, user_scopes: Sequence[Scope] = tuple()
    ):
        cursor = self._fragments.aggregate(
            [*aggregate_latest(user_scopes), {"$project": {"joins": False}}]
        )
        return self._map_fragments(cursor)

    def query_by_transliterated_not_revised_by_other(
        self, user_scopes: Sequence[Scope] = tuple()
    ):
        cursor = self._fragments.aggregate(
            [*aggregate_needs_revision(user_scopes), {"$project": {"joins": False}}],
            allowDiskUse=True,
        )
        return FragmentInfoSchema(many=True).load(cursor)

    def update_field(self, field, fragment):

        fields_to_update = {
            "introduction": ("introduction",),
            "lemmatization": ("text",),
            "genres": ("genres",),
            "references": ("references",),
            "script": ("script",),
            "transliteration": (
                "text",
                "notes",
                "signs",
                "record",
                "line_to_vec",
            ),
        }

        if field not in fields_to_update:
            raise ValueError(
                f"Unexpected update field {field}, must be one of {','.join(fields_to_update)}"
            )
        self._fragments.update_one(
            fragment_is(fragment),
            {"$set": FragmentSchema(only=fields_to_update[field]).dump(fragment)},
        )

    def query_next_and_previous_folio(self, folio_name, folio_number, number):
        sort_ascending = {"$sort": {"key": 1}}
        sort_descending = {"$sort": {"key": -1}}

        def create_pipeline(*parts):
            return [
                {"$match": {"folios.name": folio_name}},
                {"$unwind": "$folios"},
                {
                    "$project": {
                        "name": "$folios.name",
                        "number": "$folios.number",
                        "key": {"$concat": ["$folios.number", "-", "$_id"]},
                    }
                },
                {"$match": {"name": folio_name}},
                *parts,
                {"$limit": 1},
            ]

        def get_numbers(pipeline):
            cursor = self._fragments.aggregate(pipeline)
            try:
                entry = next(cursor)
                return {"fragmentNumber": entry["_id"], "folioNumber": entry["number"]}
            except StopIteration:
                return None

        first = create_pipeline(sort_ascending)
        previous = create_pipeline(
            {"$match": {"key": {"$lt": f"{folio_number}-{number}"}}}, sort_descending
        )
        next_ = create_pipeline(
            {"$match": {"key": {"$gt": f"{folio_number}-{number}"}}}, sort_ascending
        )
        last = create_pipeline(sort_descending)

        result = {
            "previous": get_numbers(previous) or get_numbers(last),
            "next": get_numbers(next_) or get_numbers(first),
        }

        if has_none_values(result):
            raise NotFoundError("Could not retrieve any fragments")
        else:
            return result

    def query_museum_numbers(self, prefix: str, number_regex: str) -> Sequence[dict]:
        return self._fragments.find_many(
            {
                "museumNumber.prefix": prefix,
                "museumNumber.number": {"$regex": number_regex},
            },
            projection={"museumNumber": True},
        )

    def _query_next_and_previous_fragment(
        self, museum_number
    ) -> Tuple[Optional[MuseumNumber], Optional[MuseumNumber]]:
        same_museum_numbers = self.query_museum_numbers(
            museum_number.prefix, rf"{museum_number.number}[^\d]*"
        )
        preeceding_museum_numbers = self.query_museum_numbers(
            museum_number.prefix, rf"{int(museum_number.number) - 1}[^\d]*"
        )
        following_museum_numbers = self.query_museum_numbers(
            museum_number.prefix, rf"{int(museum_number.number) + 1}[^\d]*"
        )
        return _find_adjacent_museum_number_from_sequence(
            museum_number,
            [
                *same_museum_numbers,
                *preeceding_museum_numbers,
                *following_museum_numbers,
            ],
        )

    def query_next_and_previous_fragment(
        self, museum_number: MuseumNumber
    ) -> FragmentPagerInfo:

        if museum_number.number.isnumeric():
            prev, next = self._query_next_and_previous_fragment(museum_number)
            if prev and next:
                return FragmentPagerInfo(prev, next)

        museum_numbers_by_prefix = self._fragments.find_many(
            {"museumNumber.prefix": museum_number.prefix},
            projection={"museumNumber": True},
        )
        prev, next = _find_adjacent_museum_number_from_sequence(
            museum_number, museum_numbers_by_prefix
        )
        if not (prev and next):
            all_museum_numbers = self._fragments.find_many(
                {}, projection={"museumNumber": True}
            )
            prev, next = _find_adjacent_museum_number_from_sequence(
                museum_number, all_museum_numbers, True
            )
        return FragmentPagerInfo(cast(MuseumNumber, prev), cast(MuseumNumber, next))

    def _map_fragments(self, cursor) -> Sequence[Fragment]:
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)

    def query(self, query: dict, user_scopes: Sequence[Scope] = tuple()) -> QueryResult:

        if set(query) - {"lemmaOperator"}:
            matcher = PatternMatcher(query, user_scopes)
            data = next(
                self._fragments.aggregate(
                    matcher.build_pipeline(),
                    collation=Collation(
                        locale="en", numericOrdering=True, alternate="shifted"
                    ),
                ),
                None,
            )
        else:
            data = None

        return QueryResultSchema().load(data) if data else QueryResult.create_empty()
