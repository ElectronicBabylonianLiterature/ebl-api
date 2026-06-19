from marshmallow import Schema, fields, post_dump, post_load, validate
from ebl.common.query.query_result import (
    CorpusQueryItem,
    CorpusQueryResult,
    QueryItem,
    QueryResult,
    AfORegisterToFragmentQueryResult,
    AfORegisterToFragmentQueryItem,
)
from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.schemas import StageField

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


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
    stage = StageField(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    lines = fields.List(fields.Integer(), required=True)
    variants = fields.List(fields.Integer(), required=True)
    match_count = fields.Integer(required=True, data_key="matchCount")

    @post_load
    def make_query_item(self, data, **kwargs) -> CorpusQueryItem:
        data["lines"] = tuple(data["lines"])
        data["variants"] = tuple(data["variants"])
        return CorpusQueryItem(**data)


class AfORegisterToFragmentQueryItemSchema(Schema):
    traditional_reference = fields.String(
        required=True, data_key="traditionalReference"
    )
    fragment_numbers = fields.List(
        fields.String(), required=True, data_key="fragmentNumbers"
    )

    @post_load
    def make_query_item(self, data, **kwargs) -> AfORegisterToFragmentQueryItem:
        data["fragment_numbers"] = tuple(data["fragment_numbers"])
        return AfORegisterToFragmentQueryItem(**data)


class QueryResultSchema(Schema):
    match_count_total = fields.Integer(
        data_key="matchCountTotal", required=True, allow_none=True
    )
    is_match_count_total_exact = fields.Boolean(
        data_key="isMatchCountTotalExact", load_default=True, dump_default=True
    )
    has_next_page = fields.Boolean(
        data_key="hasNextPage", load_default=None, dump_default=None, allow_none=True
    )
    show_count_metadata = fields.Boolean(
        data_key="_showCountMetadata", load_default=False, dump_default=False
    )
    items = fields.Nested(QueryItemSchema, many=True, required=True)

    @post_dump
    def filter_count_metadata(self, data, **kwargs):
        show_count_metadata = data.pop("_showCountMetadata", False)
        if not show_count_metadata:
            data.pop("isMatchCountTotalExact", None)
            data.pop("hasNextPage", None)
        return data

    @post_load
    def make_query_result(self, data, **kwargs) -> QueryResult:
        return QueryResult(**data)


class CorpusQueryResultSchema(QueryResultSchema):
    items = fields.Nested(CorpusQueryItemSchema, many=True, required=True)

    @post_load
    def make_query_result(self, data, **kwargs) -> CorpusQueryResult:
        return CorpusQueryResult(**data)


class AfORegisterToFragmentQueryResultSchema(Schema):
    items = fields.Nested(
        AfORegisterToFragmentQueryItemSchema, many=True, required=True
    )

    @post_load
    def make_query_result(self, data, **kwargs) -> AfORegisterToFragmentQueryResult:
        return AfORegisterToFragmentQueryResult(**data)
