from marshmallow import Schema, fields, post_load

from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.schemas import NameEnumField


class ReferenceSchema(Schema):
    id = fields.String(required=True)
    type = NameEnumField(ReferenceType, required=True)
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(), required=True, data_key="linesCited")
    document = fields.Mapping(load_default=None, load_only=True)

    @post_load
    def make_reference(self, data, **kwargs) -> Reference:
        data["id"] = BibliographyId(data["id"])
        data["lines_cited"] = tuple(data["lines_cited"])
        data["document"] = data["document"] and create_object_entry(data["document"])
        return Reference(**data)


class ApiReferenceSchema(ReferenceSchema):
    document = fields.Mapping(load_default=None)
