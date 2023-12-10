from marshmallow import Schema, fields, post_load, EXCLUDE
from typing import cast, Sequence
from pymongo.database import Database
from natsort import natsorted
from ebl.mongo_collection import MongoCollection
from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)
from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from ebl.common.query.query_collation import (
    make_query_params,
)


COLLECTION = "afo_register"


def create_search_query(query):
    if "textNumber" not in query:
        return query
    text_number = query["textNumber"]
    text_number_stripped = text_number.strip('"')
    if text_number != text_number_stripped:
        query["textNumber"] = text_number_stripped
    else:
        query["textNumber"] = {"$regex": f"^{text_number}", "$options": "i"}
    return query


def cast_with_sorting(
    records: Sequence[AfoRegisterRecord],
) -> Sequence[AfoRegisterRecord]:
    return cast(
        Sequence[AfoRegisterRecord],
        natsorted(records, key=lambda record: f"${record.text} ${record.text_number}"),
    )


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
        data["text_numbers"] = natsorted(data["text_numbers"])
        return AfoRegisterRecordSuggestion(**data)


class MongoAfoRegisterRepository(AfoRegisterRepository):
    def __init__(self, database: Database):
        self._afo_register = MongoCollection(database, COLLECTION)

    def create(self, afo_register_record: AfoRegisterRecord) -> str:
        return self._afo_register.insert_one(
            AfoRegisterRecordSchema().dump(afo_register_record)
        )

    def search(self, query, *args, **kwargs) -> Sequence[AfoRegisterRecord]:
        data = self._afo_register.find_many(create_search_query(query))
        records = AfoRegisterRecordSchema().load(data, many=True)
        return cast_with_sorting(records)

    def search_by_texts_and_numbers(
        self, query_list: Sequence[str], *args, **kwargs
    ) -> Sequence[AfoRegisterRecord]:
        pipeline = [
            {
                "$addFields": {
                    "combined_field": {"$concat": ["$text", " ", "$textNumber"]}
                }
            },
            {"$match": {"combined_field": {"$in": query_list}}},
            {"$group": {"_id": "$_id", "document": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$document"}},
            {"$project": {"combined_field": 0}},
        ]
        data = self._afo_register.aggregate(pipeline)
        records = AfoRegisterRecordSchema().load(data, many=True)
        return cast_with_sorting(records)

    def search_suggestions(
        self, text_query: str, *args, **kwargs
    ) -> Sequence[AfoRegisterRecordSuggestion]:
        collated_query_iter = iter(make_query_params({"text": text_query}, "afo-register"))
        collated_query = next(collated_query_iter)
        pipeline = [
            {"$match": {"text": {"$regex": collated_query.value, "$options": "i"}}},
            {"$group": {"_id": "$text", "textNumbers": {"$addToSet": "$textNumber"}}},
            {
                "$project": {
                    "text": "$_id",
                    "_id": 0,
                    "textNumbers": {"$setUnion": ["$textNumbers", []]},
                }
            },
            {"$unwind": "$textNumbers"},
            {"$sort": {"textNumbers": 1}},
            {"$group": {"_id": "$text", "textNumbers": {"$push": "$textNumbers"}}},
            {"$project": {"text": "$_id", "textNumbers": "$textNumbers", "_id": 0}},
        ]
        suggestions = AfoRegisterRecordSuggestionSchema().load(
            self._afo_register.aggregate(pipeline), many=True
        )
        return cast(Sequence[AfoRegisterRecordSuggestion], suggestions)
