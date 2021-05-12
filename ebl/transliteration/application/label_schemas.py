from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import (
    ColumnLabel,
    ObjectLabel,
    SurfaceLabel,
    parse_labels,
)


def labels():
    return fields.Function(
        lambda manuscript_line: [label.to_value() for label in manuscript_line.labels],
        lambda value: parse_labels(" ".join(value)),
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


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnum(atf.Surface, required=True)
    text = fields.String(default="")

    @post_load
    def make_label(self, data, **kwargs) -> SurfaceLabel:
        return SurfaceLabel(data["status"], data["surface"], data["text"])


class ObjectLabelSchema(LabelSchema):
    object = NameEnum(atf.Object, required=True)
    text = fields.String(default="")

    @post_load
    def make_label(self, data, **kwargs) -> ObjectLabel:
        return ObjectLabel(data["status"], data["object"], data["text"])
