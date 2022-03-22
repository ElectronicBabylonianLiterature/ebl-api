import operator
from typing import Callable, List, Optional, Sequence, Tuple, cast
import attr

from marshmallow import EXCLUDE
import pymongo

from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.fragmentarium.infrastructure.collections import JOINS_COLLECTION
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_latest,
    aggregate_needs_revision,
    aggregate_path_of_the_pioneers,
    aggregate_random,
    fragment_is,
    join_joins,
    number_is,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.transliteration.infrastructure.parallel_lines import (
    MongoParallelLineInjector,
)
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
        self._injector = MongoParallelLineInjector.create(database)

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

    def query_by_museum_number(self, number: MuseumNumber):
        data = self._fragments.aggregate(
            [
                {"$match": museum_number_is(number)},
                *join_reference_documents(),
                *join_joins(),
            ]
        )
        try:
            fragment_data = next(data)
            fragment_data["text"]["lines"] = self._injector.inject(
                fragment_data["text"]["lines"]
            )
            fragment = FragmentSchema(unknown=EXCLUDE).load(fragment_data)
            return attr.evolve(
                fragment,
                text=attr.evolve(
                    fragment.text,
                    lines=self._injector.inject(fragment.text.lines),
                ),
            )
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def query_by_id_and_page_in_references(self, id_: str, pages: str):
        match: dict = {"references": {"$elemMatch": {"id": id_}}}
        if pages:
            match["references"]["$elemMatch"]["pages"] = {
                "$regex": rf".*?(^|[^\d]){pages}([^\d]|$).*?"
            }
        cursor = self._fragments.find_many(match, projection={"joins": False})
        return self._map_fragments(cursor)

    def query_by_fragment_cdli_or_accession_number(self, number):
        cursor = self._fragments.find_many(
            number_is(number), projection={"joins": False}
        )

        return self._map_fragments(cursor)

    def query_random_by_transliterated(self):
        cursor = self._fragments.aggregate(
            [*aggregate_random(), {"$project": {"joins": False}}]
        )

        return self._map_fragments(cursor)

    def query_path_of_the_pioneers(self):
        cursor = self._fragments.aggregate(
            [*aggregate_path_of_the_pioneers(), {"$project": {"joins": False}}]
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
                fragment["script"],
                tuple(
                    LineToVecEncoding.from_list(line_to_vec)
                    for line_to_vec in fragment["lineToVec"]
                ),
            )
            for fragment in cursor
        ]

    def query_by_transliterated_sorted_by_date(self):
        cursor = self._fragments.aggregate(
            [*aggregate_latest(), {"$project": {"joins": False}}]
        )
        return self._map_fragments(cursor)

    def query_by_transliterated_not_revised_by_other(self):
        cursor = self._fragments.aggregate(
            [*aggregate_needs_revision(), {"$project": {"joins": False}}],
            allowDiskUse=True,
        )
        return FragmentInfoSchema(many=True).load(cursor)

    def query_by_transliteration(self, query):
        cursor = self._fragments.find_many(
            {"signs": {"$regex": query.regexp}}, limit=100, projection={"joins": False}
        )
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        self._fragments.update_one(
            fragment_is(fragment),
            {
                "$set": FragmentSchema(
                    only=("text", "notes", "signs", "record", "line_to_vec")
                ).dump(fragment)
            },
        )

    def update_genres(self, fragment):
        self._fragments.update_one(
            fragment_is(fragment),
            {"$set": FragmentSchema(only=("genres",)).dump(fragment)},
        )

    def update_lemmatization(self, fragment):
        self._fragments.update_one(
            fragment_is(fragment),
            {"$set": FragmentSchema(only=("text",)).dump(fragment)},
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

    def update_references(self, fragment):
        self._fragments.update_one(
            fragment_is(fragment),
            {"$set": FragmentSchema(only=("references",)).dump(fragment)},
        )

    def _map_fragments(self, cursor):
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
