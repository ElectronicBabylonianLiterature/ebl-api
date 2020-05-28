from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel


class LabelSchema(Schema):  # pyre-ignore[11]
    status = fields.List(NameEnum(atf.Status), required=True)  # pyre-ignore[18]


class ColumnLabelSchema(LabelSchema):
    column = fields.Int(required=True)

    @post_load
    def make_label(self, data, **kwargs) -> ColumnLabel:
        return ColumnLabel(data["status"], data["column"])


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnum(atf.Surface, required=True)
    text = fields.String(default="")
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_label(self, data, **kwargs) -> SurfaceLabel:
        return SurfaceLabel(data["status"], data["surface"], data["text"])
