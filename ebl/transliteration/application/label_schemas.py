from marshmallow import Schema, fields, post_load  # pyre-ignore[21]

from ebl.schemas import NameEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel


class LabelSchema(Schema):  # pyre-ignore[11]
    status = fields.List(NameEnum(atf.Status), required=True)


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
