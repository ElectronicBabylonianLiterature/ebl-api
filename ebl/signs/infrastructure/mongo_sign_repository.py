import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, cast

from marshmallow import EXCLUDE
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.signs.infrastructure.sign_unicode_lookup import get_unicode_from_atf
from ebl.signs.infrastructure.sign_schemas import (
    COLLECTION,
    OrderedSignSchema,
    SignDtoSchema,
    SignSchema,
)
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignName

__all__ = ["COLLECTION", "MongoSignRepository", "SignDtoSchema", "SignSchema"]


class MongoSignRepository(SignRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, sign: Sign) -> str:
        return self._collection.insert_one(SignSchema().dump(sign))

    def _load_signs(self, documents: Iterable[Mapping[str, Any]]) -> Sequence[Sign]:
        return cast(
            Sequence[Sign], SignSchema().load(documents, unknown=EXCLUDE, many=True)
        )

    def find_many(self, query, *args, **kwargs) -> Sequence[Sign]:
        return self._load_signs(self._collection.find_many(query, *args, **kwargs))

    def find(self, name: SignName) -> Sign:
        data = self._collection.find_one_by_id(name)
        return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))

    def find_signs_by_order(self, name: SignName, sort_era: str) -> list[list[Sign]]:
        try:
            keys = self._collection.find_one_by_id(name)["sortKeys"][sort_era]
        except (KeyError, NotFoundError):
            return []

        all_results = []
        for key in keys:
            range_start = key - 5
            range_end = key + 5
            cursor = self._collection.aggregate(
                [
                    {
                        "$match": {
                            f"sortKeys.{sort_era}": {
                                "$elemMatch": {
                                    "$gte": range_start,
                                    "$lte": range_end,
                                }
                            }
                        }
                    },
                    {"$unwind": f"$sortKeys.{sort_era}"},
                    {
                        "$match": {
                            f"sortKeys.{sort_era}": {
                                "$gte": range_start,
                                "$lte": range_end,
                            }
                        }
                    },
                    {
                        "$project": {
                            "unicode": 1,
                            "name": "$_id",
                            "sort_key": f"$sortKeys.{sort_era}",
                            "mzlNumber": {
                                "$first": {
                                    "$filter": {
                                        "input": "$lists",
                                        "as": "item",
                                        "cond": {"$eq": ["$$item.name", "MZL"]},
                                    }
                                }
                            },
                        }
                    },
                    {"$sort": {"sort_key": 1}},
                    {
                        "$project": {
                            "_id": 0,
                            "name": 1,
                            "unicode": 1,
                            "mzlNumber": "$mzlNumber.number",
                        }
                    },
                    {"$group": {"_id": None, "signs": {"$push": "$$ROOT"}}},
                ]
            )

            results = [
                OrderedSignSchema().load(sign, unknown=EXCLUDE)
                for item in cursor
                for sign in item["signs"]
            ]
            all_results.extend([results])
        return all_results

    def search(self, reading: str, sub_index: Optional[int] = None) -> Optional[Sign]:
        sub_index_query = {"$exists": False} if sub_index is None else sub_index
        try:
            data = self._collection.find_one(
                {
                    "values": {
                        "$elemMatch": {"value": reading, "subIndex": sub_index_query}
                    }
                }
            )
            return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))
        except NotFoundError:
            return None

    def search_by_id(self, query: str) -> Sequence[Sign]:
        cursor = self._collection.aggregate(
            [{"$match": {"_id": {"$regex": re.escape(query), "$options": "i"}}}]
        )
        return self._load_signs(cursor)

    def search_all(self, reading: str, sub_index: int) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"values": {"$elemMatch": {"value": reading, "subIndex": sub_index}}}
        )
        return self._load_signs(cursor)

    def search_by_lists_name(self, name: str, number: str) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"lists": {"$elemMatch": {"name": name, "number": number}}}
        )
        return self._load_signs(cursor)

    def search_include_homophones(self, reading: str) -> Sequence[Sign]:
        cursor = self._collection.aggregate(
            [
                {"$match": {"values.value": reading}},
                {"$unwind": "$values"},
                {
                    "$addFields": {
                        "subIndexCopy": {
                            "$cond": [
                                {"$eq": ["$values.value", reading]},
                                {"$ifNull": ["$values.subIndex", float("inf")]},
                                float("inf"),
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$_id",
                        "lists": {"$first": "$lists"},
                        "unicode": {"$first": "$unicode"},
                        "mesZl": {"$first": "$mesZl"},
                        "LaBaSi": {"$first": "$LaBaSi"},
                        "reverseOrder": {"$first": "$reverseOrder"},
                        "logograms": {"$first": "$logograms"},
                        "fossey": {"$first": "$fossey"},
                        "sortKeys": {"$first": "$sortKeys"},
                        "values": {"$push": "$values"},
                        "subIndexCopy": {"$min": "$subIndexCopy"},
                    }
                },
                {
                    "$addFields": {
                        "logograms": {"$ifNull": ["$logograms", []]},
                        "fossey": {"$ifNull": ["$fossey", []]},
                    }
                },
                {"$sort": {"subIndexCopy": 1}},
            ]
        )
        return self._load_signs(cursor)

    def search_composite_signs(self, reading: str, sub_index: int) -> Sequence[Sign]:
        cursor = self._collection.aggregate(
            [
                {
                    "$match": {
                        "values": {
                            "$elemMatch": {"value": reading, "subIndex": sub_index}
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "signs",
                        "let": {"leftId": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$regexMatch": {
                                            "input": "$_id",
                                            "regex": {
                                                "$concat": [
                                                    r".*(^|[\.\+×&%@x|\(\)])",
                                                    {
                                                        "$trim": {
                                                            "input": "$$leftId",
                                                            "chars": "|",
                                                        }
                                                    },
                                                    r"($|[\.\+×&%@x|\(\)])",
                                                ]
                                            },
                                        }
                                    }
                                }
                            }
                        ],
                        "as": "joined",
                    }
                },
                {"$unwind": "$joined"},
                {"$replaceRoot": {"newRoot": "$joined"}},
            ]
        )
        return self._load_signs(cursor)

    def search_by_lemma(self, word_id: str) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"logograms": {"$elemMatch": {"wordId": word_id}}}
        )
        return self._load_signs(cursor)

    def list_all_signs(self) -> Sequence[str]:
        return self._collection.get_all_values("_id")

    def get_unicode_from_atf(self, line: str) -> List[Dict[str, List[int]]]:
        return get_unicode_from_atf(self._collection, line)
