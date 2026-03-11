from marshmallow import fields, post_load

from ebl.schemas import NameEnumField
from ebl.transliteration.application.label_schemas import (
    ColumnLabelSchema,
    ObjectLabelSchema,
    SurfaceLabelSchema,
)
from ebl.transliteration.application.line_schemas import LineBaseSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    CompositeAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    HeadingAtLine,
    ObjectAtLine,
    SealAtLine,
    SurfaceAtLine,
)
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)


class AtLineSchema(LineBaseSchema):
    prefix = fields.Constant("@")
    content = fields.Function(
        lambda obj: [OneOfTokenSchema().dump(ValueToken.of(obj.display_value))],
        lambda value: value,
    )


class SealAtLineSchema(AtLineSchema):
    number = fields.Int(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> SealAtLine:
        return SealAtLine(data["number"])


class HeadingAtLineSchema(AtLineSchema):
    number = fields.Int(required=True)
    display_value = fields.String(data_key="displayValue")
    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), load_default=())

    @post_load
    def make_line(self, data, **kwargs) -> HeadingAtLine:
        return HeadingAtLine(data["number"], tuple(data["parts"]))


class ColumnAtLineSchema(AtLineSchema):
    column_label = fields.Nested(ColumnLabelSchema, required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> ColumnAtLine:
        return ColumnAtLine(data["column_label"])


class DiscourseAtLineSchema(AtLineSchema):
    discourse_label = NameEnumField(atf.Discourse, required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> DiscourseAtLine:
        return DiscourseAtLine(data["discourse_label"])


class SurfaceAtLineSchema(AtLineSchema):
    surface_label = fields.Nested(SurfaceLabelSchema, required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> SurfaceAtLine:
        return SurfaceAtLine(data["surface_label"])


class ObjectAtLineSchema(AtLineSchema):
    status = fields.List(NameEnumField(atf.Status), load_only=True)
    object_label = NameEnumField(atf.Object, load_only=True)
    text = fields.String(dump_default="", load_only=True)
    label = fields.Nested(ObjectLabelSchema)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> ObjectAtLine:
        return ObjectAtLine(data["label"])


class DivisionAtLineSchema(AtLineSchema):
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, dump_default=None)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> DivisionAtLine:
        return DivisionAtLine(data["text"], data["number"])


class CompositeAtLineSchema(AtLineSchema):
    composite = NameEnumField(atf.Composite, required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, dump_default=None)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> CompositeAtLine:
        return CompositeAtLine(data["composite"], data["text"], data["number"])
