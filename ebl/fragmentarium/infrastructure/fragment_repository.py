from marshmallow import EXCLUDE  # pyre-ignore

from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_latest,
    aggregate_lemmas,
    aggregate_needs_revision,
    aggregate_path_of_the_pioneers,
    aggregate_random,
    fragment_is,
    museum_number_is,
    number_is,
)
from ebl.mongo_collection import MongoCollection
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema


COLLECTION = "fragments"


def has_none_values(dictionary: dict) -> bool:
    return not all(dictionary.values())


class MongoFragmentRepository(FragmentRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def count_transliterated_fragments(self):
        return self._collection.count_documents(HAS_TRANSLITERATION)

    def count_lines(self):
        result = self._collection.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$text.numberOfLines"}}}]
        )
        try:
            return next(result)["total"]
        except StopIteration:
            return 0

    def create(self, fragment):
        return self._collection.insert_one(
            {"_id": str(fragment.number), **FragmentSchema().dump(fragment)}
        )

    def query_by_museum_number(self, number: MuseumNumber):
        data = self._collection.find_one(museum_number_is(number))
        return FragmentSchema(unknown=EXCLUDE).load(data)  # pyre-ignore[16,28]

    def query_by_id_and_page_in_references(self, id_: str, pages: str):
        match = dict()
        match["references"] = {"$elemMatch": {"id": id_}}
        if pages:
            match["references"]["$elemMatch"]["pages"] = {
                "$regex": fr"^([^0-9]*\s*)?({pages}(-|\s)|[\d]*-{pages}\s|{pages}$)"
            }
        cursor = self._collection.find_many(match)
        return self._map_fragments(cursor)

    def query_by_fragment_cdli_or_accession_number(self, number):
        cursor = self._collection.find_many(number_is(number))

        return self._map_fragments(cursor)

    def query_random_by_transliterated(self):
        cursor = self._collection.aggregate(aggregate_random())

        return self._map_fragments(cursor)

    def query_path_of_the_pioneers(self):
        cursor = self._collection.aggregate(aggregate_path_of_the_pioneers())

        return self._map_fragments(cursor)

    def query_transliterated_numbers(self):
        cursor = self._collection.find_many(
            HAS_TRANSLITERATION, projection=["museumNumber"]
        )

        return MuseumNumberSchema(many=True).load(
            fragment["museumNumber"] for fragment in cursor
        )

    def query_by_transliterated_sorted_by_date(self):
        cursor = self._collection.aggregate(aggregate_latest())
        return self._map_fragments(cursor)

    def query_by_transliterated_not_revised_by_other(self):
        cursor = self._collection.aggregate(aggregate_needs_revision())
        return FragmentInfoSchema(many=True).load(cursor)

    def query_by_transliteration(self, query):
        cursor = self._collection.find_many(
            {"signs": {"$regex": query.regexp}}, limit=100
        )
        return self._map_fragments(cursor)

    def update_transliteration(self, fragment):
        self._collection.update_one(
            fragment_is(fragment),
            {
                "$set": FragmentSchema(only=("text", "notes", "signs", "record")).dump(
                    fragment
                )
            },
        )

    def update_genre(self, fragment):
        self._collection.update_one(
            fragment_is(fragment),
            {
                "$set": FragmentSchema(only=("genres",)).dump(
                    fragment
                )
            },
        )

    def update_lemmatization(self, fragment):
        self._collection.update_one(
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
            cursor = self._collection.aggregate(pipeline)
            if cursor.alive:
                entry = next(cursor)
                return {"fragmentNumber": entry["_id"], "folioNumber": entry["number"]}
            else:
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

    def query_next_and_previous_fragment(self, number: MuseumNumber):
        next_ = (
            self._collection.find_many({"_id": {"$gt": f"{str(number)}"}})
            .sort("_id", 1)
            .limit(1)
        )
        previous = (
            self._collection.find_many({"_id": {"$lt": f"{str(number)}"}})
            .sort("_id", -1)
            .limit(1)
        )

        def get_numbers(cursor):
            return next(cursor)["_id"] if cursor.alive else None

        first = self._collection.find_many({}).sort("_id", 1).limit(1)
        last = self._collection.find_many({}).sort("_id", -1).limit(1)
        result = {
            "previous": get_numbers(previous) or get_numbers(last),
            "next": get_numbers(next_) or get_numbers(first),
        }
        if has_none_values(result):
            raise NotFoundError("Could not retrieve any fragments")
        else:
            return result

    def query_lemmas(self, word):
        cursor = self._collection.aggregate(aggregate_lemmas(word))
        return [
            [WordId(unique_lemma) for unique_lemma in result["_id"]]
            for result in cursor
        ]

    def update_references(self, fragment):
        self._collection.update_one(
            fragment_is(fragment),
            {"$set": FragmentSchema(only=("references",)).dump(fragment)},
        )

    def _map_fragments(self, cursor):
        return FragmentSchema(unknown=EXCLUDE, many=True).load(cursor)
