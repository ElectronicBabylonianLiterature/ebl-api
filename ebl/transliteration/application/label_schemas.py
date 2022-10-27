from marshmallow import Schema, ValidationError, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import (
    ColumnLabel,
    ObjectLabel,
    SurfaceLabel,
    parse_labels,
    SealLabel,
)
from ebl.transliteration.domain.lark_parser_errors import PARSE_ERRORS


def try_parse_labels(value):
    try:
        return parse_labels(" ".join(value))
    except PARSE_ERRORS as error:
        raise ValidationError(str(error)) from error


def labels():
    return fields.Function(
        lambda manuscript_line: [label.to_value() for label in manuscript_line.labels],
        try_parse_labels,
        required=True,
    )


class LabelSchema(Schema):
    status = fields.List(NameEnum(atf.Status), required=True)
    abbreviation = fields.String()


class ColumnLabelSchema(LabelSchema):
    column = fields.Int(required=True)

    @post_load
    def make_label(self, data, **kwargs) -> ColumnLabel:
        return ColumnLabel(data["status"], data["column"])


class SealLabelSchema(LabelSchema):
    seal = fields.Int(required=True)

    @post_load
    def make_seal(self, data, **kwargs) -> SealLabel:
        return SealLabel(data["status"], data["seal"])


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnum(atf.Surface, required=True)
    text = fields.String(dump_default="")

    @post_load
    def make_label(self, data, **kwargs) -> SurfaceLabel:
        return SurfaceLabel(data["status"], data["surface"], data["text"])


class ObjectLabelSchema(LabelSchema):
    object = NameEnum(atf.Object, required=True)
    text = fields.String(dump_default="")

    @post_load
    def make_label(self, data, **kwargs) -> ObjectLabel:
        return ObjectLabel(data["status"], data["object"], data["text"])
