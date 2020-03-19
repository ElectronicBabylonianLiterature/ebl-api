from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.application.line_schemas import LineSchema
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


class SealAtLineSchema(LineSchema):
    type = fields.Constant("SealAtLine", required=True)
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SealAtLine(data["number"])


class HeadingAtLineSchema(LineSchema):
    type = fields.Constant("HeadingAtLine", required=True)
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return HeadingAtLine(data["number"])


class LabelSchema(Schema):
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


class ColumnAtLineSchema(LineSchema):
    type = fields.Constant("ColumnAtLine", required=True)
    column_label = fields.Nested(ColumnLabelSchema, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ColumnAtLine(data["column_label"])


class DiscourseAtLineSchema(LineSchema):
    type = fields.Constant("DiscourseAtLine", required=True)
    discourse_label = NameEnum(atf.Discourse, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return DiscourseAtLine(data["discourse_label"])


class SurfaceAtLineSchema(LineSchema):
    type = fields.Constant("SurfaceAtLine", required=True)
    surface_label = fields.Nested(SurfaceLabelSchema, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SurfaceAtLine(data["surface_label"])


class ObjectAtLineSchema(LineSchema):
    type = fields.Constant("ObjectAtLine", required=True)
    status = fields.List(NameEnum(atf.Status), required=True)
    object_label = NameEnum(atf.Object, required=True)
    text = fields.String(default="", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ObjectAtLine(data["status"], data["object_label"], data["text"])


class DivisionAtLineSchema(LineSchema):
    type = fields.Constant("DivisionAtLine", required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return DivisionAtLine(data["text"], data["number"])


class CompositeAtLineSchema(LineSchema):
    type = fields.Constant("CompositeAtLine", required=True)
    composite = NameEnum(atf.Composite, required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return CompositeAtLine(data["composite"], data["text"], data["number"])
