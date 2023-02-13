from typing import List, Optional
import re

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.collections import JOINS_COLLECTION
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.transliteration.infrastructure.queries import museum_number_is

HAS_TRANSLITERATION: dict = {"text.lines.type": {"$exists": True}}
NUMBER_OF_LATEST_TRANSLITERATIONS: int = 20
NUMBER_OF_NEEDS_REVISION: int = 20
PATH_OF_THE_PIONEERS_MAX_UNCURATED_REFERENCES: int = 10


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


def empty_authorized_scopes() -> dict:
    return {
        "$or": [
            {"authorizedScopes": {"$exists": False}},
            {"authorizedScopes": {"$size": 0}},
        ]
    }


def match_user_scopes(user_scopes: Optional[List[str]] = None) -> dict:
    def strip_affixes(scope: str) -> str:
        match = re.match(r"^(?:read:)(.+)(?:-.+)$", scope)
        if match:
            return match[1]
        else:
            raise ValueError(
                f"Unexpected scope format: {scope!r} does not start "
                "with 'read:' and end with '-fragments'"
            )

    if user_scopes:
        return {
            "$or": [{"authorizedScopes": strip_affixes(scope)} for scope in user_scopes]
        }
    else:
        return empty_authorized_scopes()


def aggregate_random(user_scopes: Optional[List[str]] = None) -> List[dict]:
    return [
        {"$match": {**HAS_TRANSLITERATION, **match_user_scopes(user_scopes)}},
        sample_size_one(),
    ]


def aggregate_latest(user_scopes: Optional[List[str]] = None) -> List[dict]:
    temp_field_name = "_temp"
    return [
        {
            "$match": {
                "record.type": RecordType.TRANSLITERATION.value,
                **match_user_scopes(user_scopes),
            }
        },
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


def aggregate_needs_revision(user_scopes: Optional[List[str]] = None) -> List[dict]:
    return [
        {
            "$match": {
                "record.type": "Transliteration",
                **HAS_TRANSLITERATION,
                **match_user_scopes(user_scopes),
            }
        },
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


def aggregate_path_of_the_pioneers(
    user_scopes: Optional[List[str]] = None,
) -> List[dict]:
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
                    match_user_scopes(user_scopes),
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


def is_in_fragmentarium(local_field: str, as_: str) -> List[dict]:
    return [
        {
            "$lookup": {
                "from": FRAGMENTS_COLLECTION,
                "let": {"number": f"${local_field}"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$museumNumber.prefix",
                                            "$$number.prefix",
                                        ]
                                    },
                                    {
                                        "$eq": [
                                            "$museumNumber.number",
                                            "$$number.number",
                                        ]
                                    },
                                    {
                                        "$eq": [
                                            "$museumNumber.suffix",
                                            "$$number.suffix",
                                        ]
                                    },
                                ]
                            }
                        }
                    }
                ],
                "as": as_,
            }
        },
        {"$set": {as_: {"$anyElementTrue": f"${as_}"}}},
    ]


def join_joins() -> List[dict]:
    return [
        {
            "$lookup": {
                "from": JOINS_COLLECTION,
                "let": {"number": "$museumNumber"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$anyElementTrue": {
                                    "$map": {
                                        "input": "$fragments",
                                        "as": "fragment",
                                        "in": {
                                            "$and": [
                                                {
                                                    "$eq": [
                                                        "$$fragment.museumNumber.prefix",
                                                        "$$number.prefix",
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$$fragment.museumNumber.number",
                                                        "$$number.number",
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$$fragment.museumNumber.suffix",
                                                        "$$number.suffix",
                                                    ]
                                                },
                                            ]
                                        },
                                    }
                                }
                            }
                        }
                    },
                    {"$limit": 1},
                    {"$unwind": "$fragments"},
                    *(
                        is_in_fragmentarium(
                            "fragments.museumNumber", "fragments.isInFragmentarium"
                        )
                    ),
                    {
                        "$group": {
                            "_id": "$fragments.group",
                            "fragments": {"$push": "$fragments"},
                        }
                    },
                    {"$unset": "fragments.group"},
                    {"$sort": {"_id": 1}},
                    {"$group": {"_id": None, "fragments": {"$push": "$fragments"}}},
                ],
                "as": "joins",
            }
        },
        {"$set": {"joins": {"$first": "$joins"}}},
        {"$set": {"joins": "$joins.fragments"}},
    ]
