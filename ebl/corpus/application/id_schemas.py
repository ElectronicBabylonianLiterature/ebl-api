from marshmallow import fields, post_load, Schema, validate

from ebl.corpus.domain.text_id import TextId


class TextIdSchema(Schema):
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))

    @post_load
    def make_id(self, data, **kwargs) -> TextId:
        return TextId(data["category"], data["index"])
