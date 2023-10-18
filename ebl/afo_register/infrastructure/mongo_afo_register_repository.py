from marshmallow import Schema, fields, post_load
from typing import cast
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord
from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository


COLLECTION = "afo_register"


class AfoRegisterRecordSchema(Schema):
    afo_number = fields.String(required=True, data_key="afoNumber")
    page = fields.String(required=True)
    text = fields.String(required=True)
    text_number = fields.String(required=True, data_key="textNumber")
    lines_discussed = fields.String(data_key="linesDiscussed")
    discussed_by = fields.String(data_key="discussedBy")
    discussed_by_notes = fields.String(data_key="discussedByNotes")

    @post_load
    def make_record(self, data, **kwargs):
        return AfoRegisterRecord(**data)


class MongoAfoRegisterRepository(AfoRegisterRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def find(self, query, *args, **kwargs) -> AfoRegisterRecord:
        data = {}  # self._collection.find_one_by_id(name)
        return cast(AfoRegisterRecord, AfoRegisterRecordSchema().load(data))
