from typing import List, Optional, Sequence, Iterator

import pymongo
from marshmallow import EXCLUDE

from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import (
    QueryResultSchema,
)
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.date import Date, DateSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_needs_revision,
    aggregate_path_of_the_pioneers,
    aggregate_random,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.queries import query_number_is


RETRIEVE_ALL_LIMIT = 1000


def has_none_values(dictionary: dict) -> bool:
    return not all(dictionary.values())


def load_museum_number(data: dict) -> MuseumNumber:
    return MuseumNumberSchema().load(data.get("museumNumber", data))


def load_query_result(cursor: Iterator) -> QueryResult:
    data = next(cursor, None)
    return QueryResultSchema().load(data) if data else QueryResult.create_empty()


class MongoFragmentRepositoryGetExtended(FragmentRepository):
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

    def query_by_transliterated_not_revised_by_other(
        self, user_scopes: Sequence[Scope] = tuple()
    ):
        cursor = self._fragments.aggregate(
            [*aggregate_needs_revision(user_scopes), {"$project": {"joins": False}}],
            allowDiskUse=True,
        )
        return FragmentInfoSchema(many=True).load(cursor)

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

    def fetch_fragment_signs(self) -> Sequence[dict]:
        return list(
            self._fragments.find_many(
                {"signs": {"$regex": "."}}, projection={"signs": True}
            )
        )

    def fetch_date(self, number: MuseumNumber) -> Optional[Date]:
        try:
            if date := self._fragments.find_one(
                {
                    "museumNumber.prefix": number.prefix,
                    "museumNumber.number": number.number,
                    "museumNumber.suffix": number.suffix,
                },
                projection={"date": True},
            ).get("date"):
                return DateSchema(unknown=EXCLUDE).load(date)
            return None
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def fetch_scopes(self, number: MuseumNumber) -> List[Scope]:
        fragment = next(
            self._fragments.find_many(
                query_number_is(number), projection={"authorizedScopes": True}
            ),
            {},
        )
        return [
            Scope.from_string(f"read:{value}-fragments")
            for value in fragment.get("authorizedScopes", [])
        ]
