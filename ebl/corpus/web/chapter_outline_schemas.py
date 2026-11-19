from typing import Sequence

from marshmallow import Schema, fields

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.domain.chapter import Classification
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.schemas import StageField, ValueEnumField

LINE_TOKEN_FIELDS: Sequence[str] = (
    "variants.reconstructionTokens",
    "variants.manuscripts.atfTokens",
)
LINES_PAGE_TOKEN_FIELDS: Sequence[str] = tuple(
    f"lines.{field}" for field in LINE_TOKEN_FIELDS
)


class ManuscriptOutlineSchema(Schema):
    id = fields.Integer(required=True)
    siglum = fields.String(required=True)
    museum_number = fields.String(required=True, data_key="museumNumber")
    accession = fields.String(required=True)


class LineVariantOutlineSchema(Schema):
    reconstruction = fields.String(required=True)
    manuscript_ids = fields.List(
        fields.Integer(), required=True, data_key="manuscriptIds"
    )


class LineOutlineSchema(Schema):
    index = fields.Integer(required=True)
    number = fields.String(required=True)
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    translation = fields.String(required=True)
    variants = fields.Nested(LineVariantOutlineSchema, many=True, required=True)


class ChapterOutlineSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    classification = ValueEnumField(Classification, required=True)
    stage = StageField(required=True)
    version = fields.String(required=True)
    name = fields.String(required=True)
    order = fields.Integer(required=True)
    uncertain_fragments = fields.List(
        fields.String(), required=True, data_key="uncertainFragments"
    )
    manuscripts = fields.Nested(ManuscriptOutlineSchema, many=True, required=True)
    lines = fields.Nested(LineOutlineSchema, many=True, required=True)


class LinesPageSchema(Schema):
    total = fields.Integer(required=True)
    offset = fields.Integer(required=True)
    limit = fields.Integer(required=True)
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


def create_lines_page_schema(include_tokens: bool) -> LinesPageSchema:
    return LinesPageSchema(exclude=() if include_tokens else LINES_PAGE_TOKEN_FIELDS)
