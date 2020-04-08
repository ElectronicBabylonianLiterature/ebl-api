from marshmallow import Schema, fields, post_load  # pyre-ignore

from ebl.schemas import NameEnum
from ebl.transliteration.application.line_schemas import DollarAndAtLineSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    SealAtLine,
    HeadingAtLine,
    ColumnAtLine,
    SurfaceAtLine,
    ObjectAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    CompositeAtLine,
)
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel


class SealAtLineSchema(DollarAndAtLineSchema):
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SealAtLine(data["number"])


class HeadingAtLineSchema(DollarAndAtLineSchema):
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return HeadingAtLine(data["number"])


class LabelSchema(Schema):  # pyre-ignore[11]
    status = fields.List(NameEnum(atf.Status), required=True)


class ColumnLabelSchema(LabelSchema):
    column = fields.Int(required=True)

    @post_load
    def make_label(self, data, **kwargs):
        return ColumnLabel(data["status"], data["column"])


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnum(atf.Surface, required=True)
    text = fields.String(default="")

    @post_load
    def make_label(self, data, **kwargs):
        return SurfaceLabel(data["status"], data["surface"], data["text"])


class ColumnAtLineSchema(DollarAndAtLineSchema):
    column_label = fields.Nested(
        ColumnLabelSchema, required=True
    )

    @post_load
    def make_line(self, data, **kwargs):
        return ColumnAtLine(data["column_label"])


class DiscourseAtLineSchema(DollarAndAtLineSchema):
    discourse_label = NameEnum(atf.Discourse, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return DiscourseAtLine(data["discourse_label"])


class SurfaceAtLineSchema(DollarAndAtLineSchema):
    surface_label = fields.Nested(
        SurfaceLabelSchema, required=True
    )

    @post_load
    def make_line(self, data, **kwargs):
        return SurfaceAtLine(data["surface_label"])


class ObjectAtLineSchema(DollarAndAtLineSchema):
    status = fields.List(NameEnum(atf.Status), required=True)
    object_label = NameEnum(atf.Object, required=True)
    text = fields.String(default="", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ObjectAtLine(data["status"], data["object_label"], data["text"])


class DivisionAtLineSchema(DollarAndAtLineSchema):
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return DivisionAtLine(data["text"], data["number"])


class CompositeAtLineSchema(DollarAndAtLineSchema):
    composite = NameEnum(atf.Composite, required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return CompositeAtLine(data["composite"], data["text"], data["number"])
