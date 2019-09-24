from functools import reduce
from typing import List, Optional, Sequence, Tuple, cast

import pydash
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.signlist.domain.sign import Sign, SignListRecord, Value
from ebl.transliteration_search.value import AnyKey, NameKey, ValueKey

COLLECTION = 'signs'


class SignListRecordSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_sign_list_record(self, data, **kwargs):
        return SignListRecord(**data)


class ValueSchema(Schema):
    value = fields.String(required=True)
    sub_index = fields.Int(missing=None, data_key='subIndex')

    @post_load
    def make_value(self, data, **kwargs):
        return Value(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value is not None
        }


class SignSchema(Schema):
    name = fields.String(required=True, data_key='_id',)
    lists = fields.Nested(SignListRecordSchema, many=True, required=True)
    values = fields.Nested(ValueSchema, many=True, required=True,
                           unknown=EXCLUDE)

    @post_load
    def make_sign(self, data, **kwargs) -> Sign:
        data['lists'] = tuple(data['lists'])
        data['values'] = tuple(data['values'])
        return Sign(**data)


def create_value_query(keys: Sequence[ValueKey]):
    value_queries = [
        {
            'value': value,
            'subIndex': {
                '$exists': False
            } if sub_index is None else sub_index
        } for value, sub_index in keys
    ]
    return {
        'values': {
            '$elemMatch': {
                '$or': value_queries
            }
        }
    }


def creates_name_query(keys: Sequence[NameKey]):
    return {

        '_id': {
            '$in': keys
        }
    }


def partition_keys(keys: Sequence[AnyKey]) -> Tuple[
    Sequence[ValueKey],
    Sequence[NameKey]
]:
    def partition(acc, key):
        values, names = acc
        if type(key) == tuple:
            values.append(cast(ValueKey, key))
        else:
            names.append(NameKey(key))
        return values, names

    return reduce(partition, keys, ([], []))


def create_signs_query(keys: List[AnyKey]):
    values, names = partition_keys(keys)
    sub_queries: list = []
    if values:
        sub_queries.append(create_value_query(values))
    if names:
        sub_queries.append(creates_name_query(names))
    return {
        '$or': sub_queries
    }


class MongoSignRepository:

    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, sign: Sign) -> str:
        return self._collection.insert_one(SignSchema().dump(sign))

    def find(self, name: str) -> Sign:
        data = self._collection.find_one_by_id(name)
        return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))

    def search(self, reading, sub_index) -> Optional[Sign]:
        sub_index_query = \
            {'$exists': False} if sub_index is None else sub_index
        try:
            data = self._collection.find_one({
                'values': {
                    '$elemMatch': {
                        'value': reading,
                        'subIndex': sub_index_query
                    }
                }
            })
            return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))
        except NotFoundError:
            return None

    def search_many(self, readings: List[AnyKey]) -> List[Sign]:
        if readings:
            query = create_signs_query(readings)
            return cast(List[Sign],
                        SignSchema(unknown=EXCLUDE, many=True).load(
                            self._collection.find_many(query)
                        ))
        else:
            return []


class MemoizingSignRepository(MongoSignRepository):

    def __init__(self, database):
        super().__init__(database)
        self.search = pydash.memoize(super().search)
        self.search_many = pydash.memoize(super().search_many)
