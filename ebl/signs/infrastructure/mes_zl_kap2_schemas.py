from marshmallow import Schema, fields


class MesZlKap2EntrySchema(Schema):
    number = fields.String(required=True)
    text = fields.String(required=True)
