from marshmallow import Schema, fields, post_load, EXCLUDE
from typing import cast, Sequence
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)
from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository


COLLECTION = "afo_register"


class AfoRegisterRecordSchema(Schema):
    class Meta:
        unknown = EXCLUDE

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


class AfoRegisterRecordSuggestionSchema(Schema):
    text = fields.String(required=True)
    text_numbers = fields.List(fields.String(), required=True, data_key="textNumbers")

    @post_load
    def make_suggestion(self, data, **kwargs):
        return AfoRegisterRecordSuggestion(**data)


class MongoAfoRegisterRepository(AfoRegisterRepository):
    def __init__(self, database: Database):
        self._afo_register = MongoCollection(database, COLLECTION)

    def create(self, afo_register_record: AfoRegisterRecord) -> str:
        return self._afo_register.insert_one(
            AfoRegisterRecordSchema().dump(afo_register_record)
        )

    def search(self, query, *args, **kwargs) -> Sequence[AfoRegisterRecord]:
        records = AfoRegisterRecordSchema().load(
            self._afo_register.find_many(query), many=True
        )
        return cast(Sequence[AfoRegisterRecord], records)

    def search_suggestions(
        self, text_query: str, *args, **kwargs
    ) -> Sequence[AfoRegisterRecordSuggestion]:
        pipeline = [
            {"$match": {"text": {"$regex": text_query, "$options": "i"}}},
            {"$group": {"_id": "$text", "textNumbers": {"$push": "$textNumber"}}},
            {"$project": {"text": "$_id", "textNumbers": "$textNumbers", "_id": 0}},
        ]
        suggestions = AfoRegisterRecordSuggestionSchema().load(
            self._afo_register.aggregate(pipeline), many=True
        )
        return cast(Sequence[AfoRegisterRecordSuggestion], suggestions)
