from marshmallow import Schema, fields, post_load

from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry


class MesZlKap2EntrySchema(Schema):
    number = fields.String(required=True)
    text = fields.String(required=True)


class MesZlKap2DocumentSchema(Schema):
    number = fields.String(required=True, data_key="_id")
    text = fields.String(required=True)
    aliases = fields.List(fields.String(), required=True)

    @post_load
    def make_entry(self, data: dict, **kwargs) -> MesZlKap2Entry:
        return MesZlKap2Entry(data["number"], data["text"])
