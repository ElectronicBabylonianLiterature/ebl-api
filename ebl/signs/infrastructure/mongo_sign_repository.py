import re
from typing import List, Optional, Tuple, cast, Sequence, Dict, Iterable

from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
from pymongo.database import Database
from ebl.transliteration.domain.enclosure_tokens import Determinative
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SignName,
    Value,
    Logogram,
    Fossey,
    SortKeys,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark

COLLECTION = "signs"


class SignListRecordSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_sign_list_record(self, data, **kwargs):
        return SignListRecord(**data)


class ValueSchema(Schema):
    value = fields.String(required=True)
    sub_index = fields.Int(load_default=None, data_key="subIndex")

    @post_load
    def make_value(self, data, **kwargs):
        return Value(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class OrderedSignSchema(Schema):
    name = fields.String(required=True)
    unicode = fields.List(fields.Int(), required=True)
    mzl = fields.String(required=False, data_key="mzlNumber")


class LogogramSchema(Schema):
    logogram = fields.String(required=True)
    atf = fields.String(required=True)
    word_id = fields.List(fields.String(), required=True, data_key="wordId")
    schramm_logogramme = fields.String(required=True, data_key="schrammLogogramme")
    unicode = fields.String()

    @post_load
    def make_logogram(self, data, **kwargs) -> Logogram:
        data["word_id"] = tuple(data["word_id"])
        return Logogram(**data)


class FosseySchema(Schema):
    page = fields.Integer(required=True)
    number = fields.Integer(required=True)
    suffix = fields.String(required=True)
    reference = fields.String(required=True)
    new_edition = fields.String(required=True, data_key="newEdition")
    secondary_literature = fields.String(required=True, data_key="secondaryLiterature")
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    cdli_number = fields.String(required=True, data_key="cdliNumber")
    external_project = fields.String(required=True, data_key="externalProject")
    notes = fields.String(required=True)
    date = fields.String(required=True)
    transliteration = fields.String(required=True)
    sign = fields.String(required=True)

    @post_load
    def make_fossey(self, data, **kwargs):
        return Fossey(**data)


class SortKeysSchema(Schema):
    neo_assyrian_onset = fields.List(
        fields.Integer(),
        data_key="neoAssyrianOnset",
        allow_none=True,
        load_default=None,
    )
    neo_babylonian_onset = fields.List(
        fields.Integer(),
        data_key="neoBabylonianOnset",
        allow_none=True,
        load_default=None,
    )
    neo_assyrian_offset = fields.List(
        fields.Integer(),
        data_key="neoAssyrianOffset",
        allow_none=True,
        load_default=None,
    )
    neo_babylonian_offset = fields.List(
        fields.Integer(),
        data_key="neoBabylonianOffset",
        allow_none=True,
        load_default=None,
    )

    @post_load
    def make_sort_keys(self, data, **kwargs) -> SortKeys:
        return SortKeys(**data)


class SignSchema(Schema):
    name = fields.String(required=True, data_key="_id")
    lists = fields.Nested(SignListRecordSchema, many=True, required=True)
    values = fields.Nested(ValueSchema, many=True, required=True, unknown=EXCLUDE)
    logograms = fields.Nested(LogogramSchema, many=True, load_default=())
    fossey = fields.Nested(FosseySchema, many=True, load_default=())
    mes_zl = fields.String(data_key="mesZl", load_default="", allow_none=True)
    labasi = fields.String(data_key="LaBaSi", load_default="", allow_none=True)
    reverse_order = fields.String(
        data_key="reverseOrder", load_default="", allow_none=True
    )
    unicode = fields.List(fields.Int(), load_default=())
    sort_keys = fields.Nested(
        SortKeysSchema,
        data_key="sortKeys",
        allow_none=True,
        load_default=None,
    )

    @post_load
    def make_sign(self, data, **kwargs) -> Sign:
        data["lists"] = tuple(data["lists"])
        data["values"] = tuple(data["values"])
        data["logograms"] = tuple(data["logograms"])
        data["fossey"] = tuple(data["fossey"])
        data["unicode"] = tuple(data["unicode"])
        return Sign(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class SignDtoSchema(SignSchema):
    @post_dump
    def make_sign_dto(self, data, **kwargs) -> Dict:
        data["name"] = data.pop("_id")
        return {key: value for key, value in data.items() if value is not None}


class MongoSignRepository(SignRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, sign: Sign) -> str:
        return self._collection.insert_one(SignSchema().dump(sign))

    def find_many(self, query, *args, **kwargs):
        data = self._collection.find_many(query, *args, **kwargs)
        return cast(Sign, SignSchema(unknown=EXCLUDE).load(data, many=True))

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
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

    def search_all(self, reading: str, sub_index: int) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"values": {"$elemMatch": {"value": reading, "subIndex": sub_index}}}
        )
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

    def search_by_lists_name(self, name: str, number: str) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"lists": {"$elemMatch": {"name": name, "number": number}}}
        )
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

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
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

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
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

    def search_by_lemma(self, word_id: str) -> Sequence[Sign]:
        cursor = self._collection.find_many(
            {"logograms": {"$elemMatch": {"wordId": word_id}}}
        )
        return SignSchema().load(cursor, unknown=EXCLUDE, many=True)

    def list_all_signs(self) -> Sequence[str]:
        return self._collection.get_all_values("_id")

    def _extract_word_subIndex(self, word):
        for part in word._parts:
            if isinstance(part, Determinative):
                part = part._parts[0]
            if getattr(part, "name_parts", []):
                yield (part.name_parts[0]._value, part.sub_index)
        yield ("whitespace", 1)

    def _extract_words_subIndexes(self, result) -> Iterable[Tuple[str, int]]:
        return (
            value_index
            for line in result.lines
            for word in line._content
            for value_index in self._extract_word_subIndex(word)
        )

    def _find_unicode(
        self, values_indexes: Iterable[Tuple[str, int]]
    ) -> Iterable[Dict[str, List[int]]]:
        for value, sub_index in values_indexes:
            if value == "whitespace":
                yield {"unicode": [9999]}
            else:
                query = {
                    "values": {"$elemMatch": {"value": value, "subIndex": sub_index}}
                }
                yield from self._collection.find_many(query, {"_id": 0, "unicode": 1})

    def get_unicode_from_atf(self, line: str) -> List[Dict[str, List[int]]]:
        text = parse_atf_lark(f"1. {line}")
        values_indexes = self._extract_words_subIndexes(text)
        line_query_result = list(self._find_unicode(values_indexes))
        return line_query_result[:-1]
