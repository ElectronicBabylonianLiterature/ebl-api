from typing import List

from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.record import RecordType

HAS_TRANSLITERATION: dict = {"text.lines.type": {"$exists": True}}
NUMBER_OF_LATEST_TRANSLITERATIONS: int = 20
NUMBER_OF_NEEDS_REVISION: int = 20
PATH_OF_THE_PIONEERS_MAX_UNCURATED_REFERENCES: int = 10


def museum_number_is(number: MuseumNumber) -> dict:
    serialized = MuseumNumberSchema().dump(number)
    return {f"museumNumber.{key}": value for key, value in serialized.items()}


def fragment_is(fragment: Fragment) -> dict:
    return museum_number_is(fragment.number)


def number_is(number: str) -> dict:
    or_ = [{"cdliNumber": number}, {"accession": number}]
    try:
        or_.append(museum_number_is(MuseumNumber.of(number)))
    except ValueError:
        pass
    return {"$or": or_}


def sample_size_one() -> dict:
    return {"$sample": {"size": 1}}


def aggregate_random() -> List[dict]:
    return [{"$match": HAS_TRANSLITERATION}, sample_size_one()]


def aggregate_latest() -> List[dict]:
    temp_field_name = "_temp"
    return [
        {"$match": {"record.type": RecordType.TRANSLITERATION.value}},
        {
            "$addFields": {
                temp_field_name: {
                    "$filter": {
                        "input": "$record",
                        "as": "entry",
                        "cond": {
                            "$eq": ["$$entry.type", RecordType.TRANSLITERATION.value]
                        },
                    }
                }
            }
        },
        {"$sort": {f"{temp_field_name}.date": -1}},
        {"$limit": NUMBER_OF_LATEST_TRANSLITERATIONS},
        {"$project": {temp_field_name: 0}},
    ]


def aggregate_needs_revision() -> List[dict]:
    return [
        {"$match": {"record.type": "Transliteration", **HAS_TRANSLITERATION}},
        {"$unwind": "$record"},
        {"$sort": {"record.date": 1}},
        {
            "$group": {
                "_id": "$museumNumber",
                "accession": {"$first": "$accession"},
                "description": {"$first": "$description"},
                "script": {"$first": "$script"},
                "record": {"$push": "$record"},
            }
        },
        {
            "$addFields": {
                "transliterations": {
                    "$filter": {
                        "input": "$record",
                        "as": "item",
                        "cond": {"$eq": ["$$item.type", "Transliteration"]},
                    }
                },
                "revisions": {
                    "$filter": {
                        "input": "$record",
                        "as": "item",
                        "cond": {"$eq": ["$$item.type", "Revision"]},
                    }
                },
            }
        },
        {
            "$addFields": {
                "transliterators": {
                    "$map": {
                        "input": "$transliterations",
                        "as": "item",
                        "in": "$$item.user",
                    }
                },
                "transliterationDates": {
                    "$map": {
                        "input": "$transliterations",
                        "as": "item",
                        "in": "$$item.date",
                    }
                },
                "revisors": {
                    "$map": {"input": "$revisions", "as": "item", "in": "$$item.user"}
                },
            }
        },
        {
            "$match": {
                "$expr": {
                    "$eq": [{"$setDifference": ["$revisors", "$transliterators"]}, []]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "number": "$_id",
                "accession": 1,
                "description": 1,
                "script": 1,
                "editionDate": {"$arrayElemAt": ["$transliterationDates", 0]},
                "editor": {"$arrayElemAt": ["$transliterators", 0]},
            }
        },
        {"$sort": {"editionDate": 1}},
        {"$limit": NUMBER_OF_NEEDS_REVISION},
    ]


def aggregate_path_of_the_pioneers() -> List[dict]:
    max_uncurated_reference = (
        f"uncuratedReferences.{PATH_OF_THE_PIONEERS_MAX_UNCURATED_REFERENCES}"
    )
    return [
        {
            "$match": {
                "$and": [
                    {"text.lines": []},
                    {"notes": ""},
                    {"$or": [{"collection": "Kuyunjik"}, {"isInteresting": True}]},
                    {"uncuratedReferences": {"$exists": True}},
                    {max_uncurated_reference: {"$exists": False}},
                    {"references.type": {"$ne": "EDITION"}},
                ]
            }
        },
        {
            "$addFields": {
                "filename": {
                    "$concat": [
                        "$museumNumber.prefix",
                        ".",
                        "$museumNumber.number",
                        {
                            "$cond": {
                                "if": {"$eq": ["$museumNumber.suffix", ""]},
                                "then": "",
                                "else": {"$concat": [".", "$museumNumber.suffix"]},
                            }
                        },
                        ".jpg",
                    ]
                }
            }
        },
        {
            "$lookup": {
                "from": "photos.files",
                "localField": "filename",
                "foreignField": "filename",
                "as": "photos",
            }
        },
        {"$match": {"photos.0": {"$exists": True}}},
        {"$project": {"photos": 0, "filename": 0}},
        sample_size_one(),
    ]
