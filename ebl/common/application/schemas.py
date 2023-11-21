from marshmallow import Schema, fields, validate, post_load
from ebl.common.domain.accession import Accession


class AbstractMuseumNumberSchema(Schema):
    prefix = fields.String(required=True, validate=validate.Length(min=1))
    number = fields.String(
        required=True, validate=(validate.Length(min=1), validate.ContainsNoneOf("."))
    )
    suffix = fields.String(required=True, validate=validate.ContainsNoneOf("."))


class AccessionSchema(AbstractMuseumNumberSchema):
    @post_load
    def create_accession(self, data, **kwargs) -> Accession:
        return Accession(**data)
