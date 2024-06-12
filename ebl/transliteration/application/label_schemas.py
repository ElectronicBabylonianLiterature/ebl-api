from marshmallow import Schema, ValidationError, fields, post_load

from ebl.schemas import NameEnumField
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import (
    ColumnLabel,
    ObjectLabel,
    SurfaceLabel,
    parse_labels,
)
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS


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
    status = fields.List(NameEnumField(atf.Status), required=True)
    abbreviation = fields.String()


class ColumnLabelSchema(LabelSchema):
    column = fields.Int(required=True)

    @post_load
    def make_label(self, data, **kwargs) -> ColumnLabel:
        return ColumnLabel(data["status"], data["column"])


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnumField(atf.Surface, required=True)
    text = fields.String(dump_default="")

    @post_load
    def make_label(self, data, **kwargs) -> SurfaceLabel:
        return SurfaceLabel(data["status"], data["surface"], data["text"])


class ObjectLabelSchema(LabelSchema):
    object = NameEnumField(atf.Object, required=True)
    text = fields.String(dump_default="")

    @post_load
    def make_label(self, data, **kwargs) -> ObjectLabel:
        return ObjectLabel(data["status"], data["object"], data["text"])
