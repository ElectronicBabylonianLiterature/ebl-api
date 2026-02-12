from typing import List, Sequence, Dict
from ebl.common.domain.accession import Accession
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.archaeology import ExcavationNumber

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.collections import JOINS_COLLECTION
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import (
    FRAGMENTS_COLLECTION,
    FINDSPOTS_COLLECTION,
)
from ebl.transliteration.infrastructure.queries import query_number_is

HAS_TRANSLITERATION: dict = {"text.lines.type": {"$exists": True}}
NUMBER_OF_NEEDS_REVISION: int = 20
PATH_OF_THE_PIONEERS_MAX_UNCURATED_REFERENCES: int = 10
LATEST_TRANSLITERATION_LIMIT: int = 50
LATEST_TRANSLITERATION_LINE_LIMIT: int = 3


def fragment_is(fragment: Fragment) -> dict:
    return query_number_is(fragment.number)


def number_is(number: str) -> dict:
    or_ = [{"externalNumbers.cdliNumber": number}]

    for number_class in [MuseumNumber, Accession, ExcavationNumber]:
        try:
            or_.append(query_number_is(number_class.of(number), allow_wildcard=True))
        except ValueError:
            continue
    return {"$or": or_}


def sample_size_one() -> dict:
    return {"$sample": {"size": 1}}


def match_user_scopes(user_scopes: Sequence[Scope] = ()) -> dict:
    allowed_scopes: List[dict] = [
        {"authorizedScopes": {"$exists": False}},
        {"authorizedScopes": {"$size": 0}},
    ]

    if user_scopes:
        allowed_scopes.extend({"authorizedScopes": str(scope)} for scope in user_scopes)

    return {"$or": allowed_scopes}


def aggregate_random(user_scopes: Sequence[Scope] = ()) -> List[dict]:
    return [
        {"$match": {**HAS_TRANSLITERATION, **match_user_scopes(user_scopes)}},
        sample_size_one(),
    ]


def exclude_restricted_fragments():
    return match_user_scopes([])


def aggregate_latest() -> List[Dict]:
    tmp_record = "_tmpRecord"
    return [
        {
            "$match": {
                "record.type": RecordType.TRANSLITERATION.value,
                **exclude_restricted_fragments(),
            }
        },
        {
            "$project": {
                tmp_record: {
                    "$filter": {
                        "input": "$record",
                        "as": "entry",
                        "cond": {
                            "$eq": [
                                "$$entry.type",
                                RecordType.TRANSLITERATION.value,
                            ]
                        },
                    }
                },
                "lineType": "$text.lines.type",
                "museumNumber": 1,
            }
        },
        {"$sort": {f"{tmp_record}.date": -1}},
        {"$limit": LATEST_TRANSLITERATION_LIMIT},
        {
            "$unwind": {
                "path": "$lineType",
                "includeArrayIndex": "lineIndex",
            }
        },
        {"$match": {"lineType": "TextLine"}},
        {
            "$group": {
                "_id": "$_id",
                "museumNumber": {"$first": "$museumNumber"},
                "matchingLines": {"$push": "$lineIndex"},
                tmp_record: {"$first": f"${tmp_record}"},
            }
        },
        {"$sort": {f"{tmp_record}.date": -1}},
        {
            "$project": {
                "_id": False,
                "museumNumber": True,
                "matchCount": {"$literal": 0},
                "matchingLines": {
                    "$slice": [
                        "$matchingLines",
                        0,
                        LATEST_TRANSLITERATION_LINE_LIMIT,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": None,
                "items": {"$push": "$$ROOT"},
            }
        },
        {"$project": {"_id": False, "items": 1, "matchCountTotal": {"$literal": 0}}},
    ]


def aggregate_needs_revision(user_scopes: Sequence[Scope] = ()) -> List[dict]:
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
    user_scopes: Sequence[Scope] = (),
) -> List[dict]:
    max_uncurated_reference = (
        f"uncuratedReferences.{PATH_OF_THE_PIONEERS_MAX_UNCURATED_REFERENCES}"
    )
    return [
        {
            "$match": {
                "$and": [
                    {"text.lines": []},
                    {"notes.text": {"$in": ["", None]}},
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


def join_findspots() -> List[dict]:
    return [
        {
            "$lookup": {
                "from": FINDSPOTS_COLLECTION,
                "localField": "archaeology.findspotId",
                "foreignField": "_id",
                "as": "findspots",
            }
        },
        {"$addFields": {"archaeology.findspot": {"$first": "$findspots"}}},
        {"$project": {"findspots": False}},
    ]


def aggregate_by_traditional_references(
    traditional_references: Sequence[str], user_scopes: Sequence[Scope] = ()
) -> List[dict]:
    return [
        {
            "$match": {
                "traditionalReferences": {"$in": traditional_references},
                **match_user_scopes(user_scopes),
            }
        },
        {"$unwind": "$traditionalReferences"},
        {"$match": {"traditionalReferences": {"$in": traditional_references}}},
        {
            "$group": {
                "_id": "$traditionalReferences",
                "fragmentNumbers": {"$addToSet": "$_id"},
            }
        },
        {
            "$project": {
                "traditionalReference": "$_id",
                "fragmentNumbers": 1,
                "_id": 0,
            }
        },
    ]
