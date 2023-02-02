from marshmallow import Schema, fields, post_load, validate
from ebl.common.query.query_result import (
    CorpusQueryItem,
    CorpusQueryResult,
    QueryItem,
    QueryResult,
)
from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.schemas import ValueEnum

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.stage import Stage


class QueryItemSchema(Schema):
    matching_lines = fields.List(
        fields.Integer(), required=True, data_key="matchingLines"
    )
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    match_count = fields.Integer(required=True, data_key="matchCount")

    @post_load
    def make_query_item(self, data, **kwargs) -> QueryItem:
        data["matching_lines"] = tuple(data["matching_lines"])
        return QueryItem(**data)


class CorpusQueryItemSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    stage = ValueEnum(Stage, required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    lines = fields.List(fields.Integer(), required=True)
    variants = fields.List(fields.Integer(), required=True)
    match_count = fields.Integer(required=True, data_key="matchCount")

    @post_load
    def make_query_item(self, data, **kwargs) -> CorpusQueryItem:
        data["lines"] = tuple(data["lines"])
        data["variants"] = tuple(data["variants"])
        return CorpusQueryItem(**data)


class QueryResultSchema(Schema):
    match_count_total = fields.Integer(data_key="matchCountTotal", required=True)
    items = fields.Nested(QueryItemSchema, many=True, required=True)

    @post_load
    def make_query_result(self, data, **kwargs) -> QueryResult:
        return QueryResult(**data)


class CorpusQueryResultSchema(QueryResultSchema):
    items = fields.Nested(CorpusQueryItemSchema, many=True, required=True)

    @post_load
    def make_query_result(self, data, **kwargs) -> CorpusQueryResult:
        return CorpusQueryResult(**data)
