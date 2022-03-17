from marshmallow import Schema, fields, post_load

from ebl.bibliography.application.reference_schema import (
    ReferenceSchema,
    ApiReferenceSchema,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.fragment_info import FragmentInfo


class FragmentInfoSchema(Schema):
    number: fields.Field = fields.Nested(MuseumNumberSchema, required=True)
    accession = fields.String(required=True)
    script = fields.String(required=True)
    description = fields.String(required=True)
    editor = fields.String(load_default="")
    edition_date = fields.String(data_key="editionDate", load_default="")
    matching_lines = fields.List(
        fields.List(fields.String()), data_key="matchingLines", load_default=tuple()
    )
    references = fields.Nested(ReferenceSchema, many=True, load_default=tuple())

    @post_load
    def make_fragment_info(self, data, **kwargs):
        data["matching_lines"] = tuple(map(tuple, data["matching_lines"]))
        return FragmentInfo(**data)


class ApiFragmentInfoSchema(FragmentInfoSchema):
    number = fields.String(dump_only=True)
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)
