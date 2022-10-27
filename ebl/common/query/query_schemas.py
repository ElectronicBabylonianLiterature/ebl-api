from typing import List
from marshmallow import Schema, fields, post_load
from ebl.common.query.query_result import QueryItem, QueryResult

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


class QueryItemSchema(Schema):
    _id: fields.String()
    museum_number: fields.Nested(MuseumNumberSchema, required=True, data_key="museumNumber")
    matching_lines: fields.List(fields.Int, load_default=tuple(), data_key="matchingLines")
    total: fields.Int(load_default=0)

    @post_load
    def make_query_item(self, data, **kwargs) -> QueryItem:
        data["matching_lines"] = tuple(data["matching_lines"])
        return QueryItem(**data)


class QueryResultSchema(Schema):
    total_matching_lines: fields.Integer(data_key="totalMatchingLines")
    items: fields.Nested(QueryItemSchema, many=True)

    @post_load
    def make_query_result(self, data, **kwargs) -> QueryResult:
        return QueryResult(data["items"], data["total_matching_lines"])
