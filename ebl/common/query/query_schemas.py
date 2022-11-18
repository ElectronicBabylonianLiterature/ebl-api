from marshmallow import Schema, fields, post_load
from ebl.common.query.query_result import QueryItem, QueryResult

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema

LemmaSequenceField = fields.List(fields.String())


class QueryItemSchema(Schema):
    id_ = fields.String(data_key="_id")
    matching_lines = fields.List(
        fields.Integer(), required=True, data_key="matchingLines"
    )
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    lemma_sequences = fields.List(
        fields.List(LemmaSequenceField),
        load_default=tuple(),
        data_key="lemmaSequences",
    )
    match_count = fields.Integer(required=True, data_key="matchCount")

    @post_load
    def make_query_item(self, data, **kwargs) -> QueryItem:
        data["matching_lines"] = tuple(data["matching_lines"])
        data["lemma_sequences"] = tuple(data["lemma_sequences"])
        return QueryItem(**data)


class QueryResultSchema(Schema):
    match_count_total = fields.Integer(data_key="matchCountTotal", required=True)
    items = fields.Nested(QueryItemSchema, many=True, required=True)

    @post_load
    def make_query_result(self, data, **kwargs) -> QueryResult:
        return QueryResult(**data)
