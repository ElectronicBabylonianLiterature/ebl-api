from typing import List, Optional, Tuple, cast

import pydash
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
from pymongo.database import Database

from ebl.mongo_repository import MongoRepository
from ebl.sign_list.sign import Sign, SignListRecord, Value

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


class MongoSignRepository(MongoRepository):

    def __init__(self, database: Database):
        super().__init__(database, COLLECTION)

    def create(self, sign: Sign) -> str:
        return super().create(SignSchema().dump(sign))

    def find(self, name: str) -> Sign:
        data = super().find(name)
        return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))

    def search(self, reading, sub_index) -> Optional[Sign]:
        sub_index_query = \
            {'$exists': False} if sub_index is None else sub_index
        data = self.get_collection().find_one({
            'values': {
                '$elemMatch': {
                    'value': reading,
                    'subIndex': sub_index_query
                }
            }
        })
        return (cast(Sign, SignSchema(unknown=EXCLUDE).load(data))
                if data else None)

    def search_many(self,
                    readings: List[Tuple[str, Optional[int]]]) -> List[Sign]:
        if readings:
            value_queries = [
                {
                    'value': reading,
                    'subIndex': {
                        '$exists': False
                    } if sub_index is None else sub_index
                } for (reading, sub_index) in readings
            ]

            return cast(List[Sign], SignSchema(unknown=EXCLUDE,
                                               many=True).load(
                self.get_collection().find({
                    'values': {
                        '$elemMatch': {
                            '$or': value_queries
                        }
                    }
                })
            ))
        else:
            return []


class MemoizingSignRepository(MongoSignRepository):

    def __init__(self, database):
        super().__init__(database)
        self.search = pydash.memoize(super().search)
        self.search_many = pydash.memoize(super().search_many)
