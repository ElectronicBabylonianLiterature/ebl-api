from marshmallow import Schema, fields, post_load  # pyre-ignore[21]
from ebl.bibliography.domain.reference import (
    BibliographyId,
    Reference,
    ReferenceType,
)
from ebl.schemas import NameEnum


class ReferenceSchema(Schema):  # pyre-ignore[11]
    id = fields.String(required=True)
    type = NameEnum(ReferenceType, required=True)
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(), required=True, data_key="linesCited")
    document = fields.Mapping(missing=None)

    @post_load
    def make_reference(self, data, **kwargs) -> Reference:
        data["id"] = BibliographyId(data["id"])
        data["lines_cited"] = tuple(data["lines_cited"])
        return Reference(**data)


class ApiReferenceSchema(ReferenceSchema):
    document = fields.Mapping(missing=None)
